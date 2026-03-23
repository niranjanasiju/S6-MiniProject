from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from dotenv import load_dotenv
import pickle
import torch
import numpy as np
import os

from rdkit import RDLogger
from torch_geometric.data import HeteroData

from schemas import (
    PredictRequest, PredictResponse,
    ADRRequest, ADRResponse,
)
from models.poly_model import load_poly_model
from models.adr_model import load_adr_model
from services.poly_service import get_fingerprint, compute_safety_score, get_ai_explanation
from services.adr_service import predict_adr, get_adr_ai_explanation

load_dotenv()
RDLogger.DisableLog('rdApp.*')

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "MedSafe AI API",
    description = """
## MedSafe AI — Drug Safety Analysis API

### Polypharmacy Interaction Checker (`/predict`)
Checks safety of adding a new drug to a patient's existing medication list.
- Morgan Fingerprints + MLP trained on **TWOSIDES** (42M FDA adverse event reports)
- Returns a **safety score (0–100)**, risk tier (SAFE / CAUTION / AVOID), and predicted side effects
- AI explanation powered by **Llama 3.3 70B** via Groq

### ADR Side Effect Predictor (`/predict-adr`)
Predicts side effects for a single drug using a knowledge graph model.
- **BioBERT + HeteroGCN** trained on **SIDER + DrugBank + Reactome**
- Returns predicted side effects grouped by category with confidence scores
- AI explanation powered by **Llama 3.3 70B** via Groq

---
> **Disclaimer:** For educational and research purposes only.
> Always consult a licensed physician before making medication decisions.
    """,
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load polypharmacy data ────────────────────────────────────────────
with open('fingerprint_dict.pkl', 'rb') as f:
    fp_dict = pickle.load(f)
with open('top_effects.pkl', 'rb') as f:
    top_effects = pickle.load(f)

poly_model = load_poly_model('best_model.pt')

# ── Load ADR mappings ─────────────────────────────────────────────────
with open('adr_mappings.pkl', 'rb') as f:
    adr_mappings = pickle.load(f)

adr_drug2idx = adr_mappings['drug2idx']
adr_idx2se = adr_mappings['idx2se']
adr_se2idx = adr_mappings['se2idx']
adr_all_drugs = adr_mappings['all_drugs']
adr_all_se = adr_mappings['all_se']

DRUG_SIDE_EFFECTS = adr_mappings.get('DRUG_SIDE_EFFECTS', {})
DRUG_TARGETS = adr_mappings['DRUG_TARGETS']
TARGET_PATHWAYS = adr_mappings['TARGET_PATHWAYS']
SIDE_EFFECT_CATEGORIES = adr_mappings['SIDE_EFFECT_CATEGORIES']

# 🔥 REQUIRED FOR SMILES
DRUG_SMILES = adr_mappings.get("DRUG_SMILES", {})

# Device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Sizes
N_ADR_DRUGS = len(adr_all_drugs)
N_ADR_SE = len(adr_all_se)

adr_tgt2idx = {t: i for i, t in enumerate(sorted(set(t for ts in DRUG_TARGETS.values() for t in ts)))}
adr_path2idx = {p: i for i, p in enumerate(sorted(set(p for ps in TARGET_PATHWAYS.values() for p in ps)))}

N_ADR_PROT = len(adr_tgt2idx)
N_ADR_PATH = len(adr_path2idx)

# ── GRAPH BUILDING (FIXED) ────────────────────────────────────────────
def to_et(pairs):
    if not pairs:
        return torch.zeros((2, 0), dtype=torch.long)
    return torch.tensor(pairs, dtype=torch.long).t().contiguous()

dse_p = [(adr_drug2idx[d], adr_se2idx[s])
         for d, ses in DRUG_SIDE_EFFECTS.items()
         for s in ses if d in adr_drug2idx and s in adr_se2idx]

dtgt_p = [(adr_drug2idx[d], adr_tgt2idx[t])
          for d, ts in DRUG_TARGETS.items()
          for t in ts if d in adr_drug2idx and t in adr_tgt2idx]

tp_p = [(adr_tgt2idx[t], adr_path2idx[p])
        for t, ps in TARGET_PATHWAYS.items()
        if t in adr_tgt2idx
        for p in ps if p in adr_path2idx]

tsm = defaultdict(set)
for d, ts in DRUG_TARGETS.items():
    if d in DRUG_SIDE_EFFECTS:
        for t in ts:
            for se in DRUG_SIDE_EFFECTS[d]:
                tsm[t].add(se)

tse_p = [(adr_tgt2idx[t], adr_se2idx[s])
         for t, ses in tsm.items()
         if t in adr_tgt2idx
         for s in ses if s in adr_se2idx]

adr_hdata = HeteroData()

adr_hdata['drug'].node_idx = torch.arange(N_ADR_DRUGS)
adr_hdata['side_effect'].node_idx = torch.arange(N_ADR_SE)
adr_hdata['protein'].node_idx = torch.arange(N_ADR_PROT)
adr_hdata['pathway'].node_idx = torch.arange(N_ADR_PATH)

E_dse, E_dtgt, E_tp, E_tse = to_et(dse_p), to_et(dtgt_p), to_et(tp_p), to_et(tse_p)

adr_hdata['drug','treats','side_effect'].edge_index = E_dse
adr_hdata['drug','targets','protein'].edge_index = E_dtgt
adr_hdata['protein','in_pathway','pathway'].edge_index = E_tp
adr_hdata['protein','causes','side_effect'].edge_index = E_tse

adr_hdata['side_effect','rev_treats','drug'].edge_index = E_dse.flip(0)
adr_hdata['protein','rev_targets','drug'].edge_index = E_dtgt.flip(0)
adr_hdata['pathway','rev_in_pathway','protein'].edge_index = E_tp.flip(0)

# ── Load ADR model ────────────────────────────────────────────────────
adr_model = load_adr_model(
    weights_path='adr_model.pt',
    n_drugs=N_ADR_DRUGS,
    n_se=N_ADR_SE,
    n_prot=N_ADR_PROT,
    n_path=N_ADR_PATH,
    all_drugs=adr_all_drugs,
    hdata=adr_hdata,
).to(DEVICE)

# ════════════════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["General"],
         summary="Health check")
def root():
    return {"message": "MedSafe AI API is running!", "version": "1.0.0"}

@app.get("/drugs/search", tags=["Polypharmacy"],
         summary="Search polypharmacy drug database")
def search_drugs(q: str):
    q_lower = q.lower().strip()
    return {"matches": [n for n in fp_dict.keys() if q_lower in n.lower()][:10]}

@app.get("/adr/drugs/search", tags=["ADR"],
         summary="Search ADR drug database")
def search_adr_drugs(q: str):
    q_lower = q.lower().strip()
    return {"matches": [n for n in adr_all_drugs if q_lower in n.lower()][:10]}

@app.post("/predict", response_model=PredictResponse,
          tags=["Polypharmacy"],
          summary="Check polypharmacy interaction safety",
          description="""
Evaluates the safety of adding a new drug to a patient's existing medication list.

**Risk tiers:** ✅ `SAFE` (≥70) | ⚠️ `CAUTION` (45–69) | 🚫 `AVOID` (<45)

**Note:** Common brand names are supported (e.g. `aspirin`, `coumadin`, `advil`).
          """)
def predict(req: PredictRequest):
    if not req.current_drugs:
        raise HTTPException(status_code=400, detail="current_drugs cannot be empty")

    fp_new = get_fingerprint(req.new_drug, fp_dict)
    if fp_new is None:
        raise HTTPException(status_code=404,
                            detail=f"Could not find drug: '{req.new_drug}'")

    results, overall_min = [], 100

    for existing in req.current_drugs:
        fp_existing = get_fingerprint(existing, fp_dict)
        if fp_existing is None:
            results.append({'pair': f"{existing} + {req.new_drug}",
                             'error': f"Could not find drug: '{existing}'"})
            continue

        x = torch.tensor(np.concatenate([fp_existing, fp_new]),
                          dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            effect_probs, _ = poly_model(x)

        effect_probs          = effect_probs.squeeze().numpy()
        safety, tier, effects = compute_safety_score(effect_probs, top_effects)
        overall_min           = min(overall_min, safety)

        ai_explanation = get_ai_explanation(
            new_drug=req.new_drug, existing_drug=existing,
            side_effects=effects[:10], safety_score=safety,
            risk_tier=tier, age=req.age, gender=req.gender,
        )
        results.append({'pair': f"{existing} + {req.new_drug}",
                         'safety_score': safety, 'risk_tier': tier,
                         'side_effects': effects[:10],
                         'ai_explanation': ai_explanation})

    overall = "SAFE" if overall_min >= 70 else ("CAUTION" if overall_min >= 45 else "AVOID")
    return {'new_drug': req.new_drug, 'current_drugs': req.current_drugs,
            'overall_verdict': overall, 'overall_score': overall_min,
            'pairs': results}

@app.post("/predict-adr", response_model=ADRResponse,
          tags=["ADR"],
          summary="Predict adverse drug reactions for a single drug",
          description="""
Predicts side effects for a single drug using BioBERT + HeteroGCN.

**Available drugs:** acetaminophen, albuterol, alprazolam, amlodipine, amoxicillin,
aspirin, atenolol, atorvastatin, cetirizine, ciprofloxacin, citalopram, clonazepam,
clopidogrel, codeine, doxycycline, escitalopram, fluoxetine, furosemide, gabapentin,
hydrochlorothiazide, ibuprofen, insulin glargine, levothyroxine, lisinopril, losartan,
metformin, methotrexate, metoprolol, montelukast, omeprazole, pantoprazole, prednisone,
quetiapine, rosuvastatin, sertraline, simvastatin, spironolactone, tamsulosin, tramadol,
venlafaxine, warfarin, zolpidem
          """)
def predict_adr_route(req: ADRRequest):
    norm = req.drug_name.lower().strip()

    predicted = predict_adr(
        drug_name=norm,
        adr_model=adr_model,
        adr_hdata=adr_hdata,
        adr_drug2idx=adr_drug2idx,
        adr_idx2se=adr_idx2se,
        DRUG_SMILES=DRUG_SMILES,   # 🔥 NEW
        SIDE_EFFECT_CATEGORIES=SIDE_EFFECT_CATEGORIES,
        N_ADR_SE=N_ADR_SE,
        threshold=req.threshold,
    )

    targets  = DRUG_TARGETS.get(norm, [])
    pathways = sorted(set(p for t in targets for p in TARGET_PATHWAYS.get(t, [])))

    ai_explanation = get_adr_ai_explanation(
        drug_name=norm, side_effects=predicted["side_effects"],
        targets=targets, pathways=pathways,
    )

    return {'drug': norm, 'threshold': req.threshold,
            'targets': targets, 'pathways': pathways,
            'side_effects': predicted["side_effects"], 'ai_explanation': ai_explanation}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)