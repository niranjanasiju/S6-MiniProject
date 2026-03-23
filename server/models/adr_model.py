import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv
from torch_geometric.data import HeteroData
from transformers import AutoTokenizer, AutoModel


ADR_EDGE_TYPES = {
    ("drug",        "treats",         "side_effect"),
    ("drug",        "targets",        "protein"),
    ("protein",     "in_pathway",     "pathway"),
    ("protein",     "causes",         "side_effect"),
    ("side_effect", "rev_treats",     "drug"),
    ("protein",     "rev_targets",    "drug"),
    ("pathway",     "rev_in_pathway", "protein"),
}


class BERTDrugEncoder(nn.Module):
    def __init__(self, out_dim=256):
        super().__init__()
        self.use_bert = False
        self.out_dim  = out_dim
        try:
            self.tok  = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
            self.bert = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
            self.proj = nn.Linear(768, out_dim)
            self.use_bert = True
            print("BioBERT loaded for ADR model!")
        except Exception:
            print("BioBERT unavailable — using CharCNN fallback.")
            self.max_len = 40
            self.ce   = nn.Embedding(128, 64, padding_idx=0)
            self.cv1  = nn.Conv1d(64, 128, 3, padding=1)
            self.cv2  = nn.Conv1d(128, out_dim, 3, padding=1)
            self.pool = nn.AdaptiveMaxPool1d(1)

    def _char_encode(self, name):
        chars = [min(ord(c), 127) for c in name.lower()[:self.max_len]]
        chars += [0] * (self.max_len - len(chars))
        x = torch.tensor(chars, dtype=torch.long,
                         device=next(self.parameters()).device).unsqueeze(0)
        return self.pool(F.relu(self.cv2(F.relu(
               self.cv1(self.ce(x).transpose(1, 2)))))).squeeze(-1)

    def forward(self, names, device=None):
        if device is None:
            device = next(self.parameters()).device
        if self.use_bert:
            enc = self.tok(names, padding=True, truncation=True,
                           max_length=32, return_tensors="pt").to(device)
            return self.proj(self.bert(**enc).last_hidden_state[:, 0, :])
        return torch.cat([self._char_encode(n) for n in names], dim=0).to(device)

class SMILESEncoder(nn.Module):
    def __init__(self, input_dim=2048, out_dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 1024),   # net.0
            nn.BatchNorm1d(1024),         # net.1
            nn.ReLU(),                    # net.2
            nn.Identity(),                # net.3  ✅ filler

            nn.Linear(1024, 512),         # net.4
            nn.BatchNorm1d(512),          # net.5
            nn.ReLU(),                    # net.6
            nn.Identity(),                # net.7  ✅ filler

            nn.Linear(512, out_dim)       # net.8
        )

    def forward(self, x):
        return self.net(x)

class ADRHeteroGCN(nn.Module):
    def __init__(self, h=256, o=256):
        super().__init__()
        self.conv1 = HeteroConv({et: SAGEConv((-1, -1), h) for et in ADR_EDGE_TYPES}, aggr="sum")
        self.conv2 = HeteroConv({et: SAGEConv((-1, -1), o) for et in ADR_EDGE_TYPES}, aggr="sum")
        self.bn1   = nn.BatchNorm1d(h)
        self.bn2   = nn.BatchNorm1d(o)

    def forward(self, x, ei):
        x = self.conv1(x, ei)
        x = {k: F.relu(self.bn1(v)) for k, v in x.items()}
        x = self.conv2(x, ei)
        x = {k: F.relu(self.bn2(v)) for k, v in x.items()}
        return x


class ADRMLPClassifier(nn.Module):
    def __init__(self, in_dim, hidden, n_cls, drop=0.4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.BatchNorm1d(hidden),
            nn.ReLU(), nn.Dropout(drop),
            nn.Linear(hidden, hidden // 2), nn.BatchNorm1d(hidden // 2),
            nn.ReLU(), nn.Dropout(drop),
            nn.Linear(hidden // 2, n_cls),
        )
    def forward(self, x):
        return self.net(x)


class DrugSideEffectModel(nn.Module):
    def __init__(self, n_d, n_se, n_p, n_pw, dim=256, drop=0.4):
        super().__init__()
        self.drug_emb   = nn.Embedding(n_d,  dim)
        self.se_emb     = nn.Embedding(n_se, dim)
        self.prot_emb   = nn.Embedding(n_p,  dim)
        self.path_emb   = nn.Embedding(n_pw, dim)
        self.bert_enc   = BERTDrugEncoder(dim)
        self.gcn        = ADRHeteroGCN(dim, dim)
        self.smiles_enc = SMILESEncoder(2048, dim)
        self.classifier = ADRMLPClassifier(
        in_dim=768,     # IMPORTANT (see below)
        hidden=1024,
        n_cls=n_se,
        drop=drop
    )

    def forward(self, drug_idx, drug_names, hdata, smiles_fp):
        dev = drug_idx.device
        x_dict = {
            "drug":        self.drug_emb(hdata["drug"].node_idx.to(dev)),
            "side_effect": self.se_emb(hdata["side_effect"].node_idx.to(dev)),
            "protein":     self.prot_emb(hdata["protein"].node_idx.to(dev)),
            "pathway":     self.path_emb(hdata["pathway"].node_idx.to(dev)),
        }
        eid      = {k: v.to(dev) for k, v in hdata.edge_index_dict.items()}
        gcn_emb  = self.gcn(x_dict, eid)["drug"][drug_idx]
        bert_emb = self.bert_enc(drug_names, device=dev)
        smiles_emb = self.smiles_enc(smiles_fp.to(dev))
        return self.classifier(torch.cat([bert_emb, gcn_emb, smiles_emb], dim=-1))

def load_adr_model(
    weights_path : str,
    n_drugs      : int,
    n_se         : int,
    n_prot       : int,
    n_path       : int,
    all_drugs    : list,
    hdata        : HeteroData,
) -> DrugSideEffectModel:
    model = DrugSideEffectModel(n_drugs, n_se, n_prot, n_path)
    model.eval()
    # Dummy forward to initialize lazy SAGEConv (needs >1 sample for BatchNorm)
    dummy_idx   = torch.tensor([0, 1], dtype=torch.long)
    dummy_names = [all_drugs[0], all_drugs[1]]
    with torch.no_grad():
        dummy_fp = torch.zeros((2, 2048))
        _ = model(dummy_idx, dummy_names, hdata, dummy_fp)
    model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    print("ADR model loaded!")
    return model