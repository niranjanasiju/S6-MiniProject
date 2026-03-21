import torch
import torch.nn as nn
import numpy as np
import pickle
import requests
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

# ── Load everything ───────────────────────────────────────────────────
with open('fingerprint_dict.pkl', 'rb') as f:
    fp_dict = pickle.load(f)

with open('top_effects.pkl', 'rb') as f:
    top_effects = pickle.load(f)

DRUG_ALIASES = {
    'aspirin'    : 'acetylsalicylic acid',
    'tylenol'    : 'acetaminophen',
    'advil'      : 'ibuprofen',
    'motrin'     : 'ibuprofen',
    'glucophage' : 'metformin',
    'coumadin'   : 'warfarin',
    'zocor'      : 'simvastatin',
    'lipitor'    : 'atorvastatin',
    'prozac'     : 'fluoxetine',
    'zoloft'     : 'sertraline',
    'prinivil'   : 'lisinopril',
    'norvasc'    : 'amlodipine',
    'synthroid'  : 'levothyroxine',
    'ventolin'   : 'albuterol',
    'lasix'      : 'furosemide',
}

SEVERITY_WEIGHTS = {
    'cardiac arrest'      : 10,
    'respiratory failure' : 10,
    'renal failure'       : 9,
    'hepatic failure'     : 9,
    'anaphylaxis'         : 9,
    'sepsis'              : 8,
    'haemorrhage'         : 8,
    'pneumonia'           : 7,
    'thrombosis'          : 7,
    'seizure'             : 7,
    'hypotension'         : 6,
    'anaemia'             : 6,
    'fall'                : 4,
    'dyspnoea'            : 5,
    'pain'                : 3,
    'asthenia'            : 3,
    'anxiety'             : 3,
    'pyrexia'             : 3,
    'dizziness'           : 2,
    'headache'            : 2,
    'fatigue'             : 2,
    'nausea'              : 2,
    'vomiting'            : 2,
    'diarrhoea'           : 2,
}

print("Checking alias:")
print(f"  'acetylsalicylic acid' in fp_dict: {'acetylsalicylic acid' in fp_dict}")

# ── Model ─────────────────────────────────────────────────────────────
class DrugInteractionModel(nn.Module):
    def __init__(self, input_dim=4096, hidden_dim=512, num_effects=50):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
        )
        self.effect_head = nn.Sequential(
            nn.Linear(128, num_effects),
            nn.Sigmoid()
        )
        self.score_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        features = self.backbone(x)
        return self.effect_head(features), self.score_head(features)

model = DrugInteractionModel()
model.load_state_dict(torch.load('best_model.pt', map_location='cpu'))
model.eval()
print("Model loaded!\n")

# ── Fingerprint helper ────────────────────────────────────────────────
def get_fingerprint(drug_name):
    key = drug_name.lower().strip()
    key = DRUG_ALIASES.get(key, key)

    if key in fp_dict:
        return fp_dict[key]

    print(f"  '{key}' not in DrugBank, trying PubChem...")
    url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug"
           f"/compound/name/{requests.utils.quote(key)}"
           f"/property/IsomericSMILES/JSON")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            smiles = r.json()['PropertyTable']['Properties'][0]['IsomericSMILES']
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
                arr = np.array(fp, dtype=np.float32)
                fp_dict[key] = arr
                return arr
    except Exception as e:
        print(f"  PubChem error: {e}")
    return None

# ── Safety score from predicted probabilities ─────────────────────────
def compute_safety_score(effect_probs, top_effects, threshold=0.25):
    risk     = 0
    detected = []

    for i, effect in enumerate(top_effects):
        prob = float(effect_probs[i])
        if prob > threshold:
            weight  = SEVERITY_WEIGHTS.get(effect, 2)
            risk   += prob * weight
            detected.append((effect, round(prob * 100, 1)))

    # max theoretical risk = 500 (all 50 effects at 100% with weight 10)
    safety = max(0, 100 - (risk / 5) * 100)
    safety = round(min(safety, 100), 1)

    if safety >= 70:
        tier = "✅ SAFE"
    elif safety >= 45:
        tier = "⚠️  CAUTION"
    else:
        tier = "🚫 AVOID"

    detected_sorted = sorted(detected, key=lambda x: -x[1])
    return safety, tier, detected_sorted

# ── Prediction function ───────────────────────────────────────────────
def predict(current_drugs, new_drug, age=40, gender='male'):
    results = []

    for existing in current_drugs:
        fp1 = get_fingerprint(existing)
        fp2 = get_fingerprint(new_drug)

        if fp1 is None:
            results.append({'pair'  : f"{existing} + {new_drug}",
                            'error' : f"Could not find: '{existing}'"})
            continue
        if fp2 is None:
            results.append({'pair'  : f"{existing} + {new_drug}",
                            'error' : f"Could not find: '{new_drug}'"})
            continue

        x = torch.tensor(
            np.concatenate([fp1, fp2]),
            dtype=torch.float32
        ).unsqueeze(0)

        with torch.no_grad():
            effect_probs, _ = model(x)   # ignore model's score head

        effect_probs = effect_probs.squeeze().numpy()
        safety, tier, detected = compute_safety_score(effect_probs, top_effects)

        results.append({
            'pair'         : f"{existing} + {new_drug}",
            'safety_score' : safety,
            'risk_tier'    : tier,
            'side_effects' : detected[:10],
        })

    return results

# ── Tests ─────────────────────────────────────────────────────────────
print("=" * 55)
print("TEST 1: Warfarin + Aspirin (known dangerous combo)")
print("=" * 55)
for r in predict(['warfarin'], 'aspirin', age=65, gender='male'):
    if 'error' in r:
        print(f"Error: {r['error']}"); continue
    print(f"Pair         : {r['pair']}")
    print(f"Safety Score : {r['safety_score']}/100  [{r['risk_tier']}]")
    print(f"Side effects :")
    for effect, prob in r['side_effects']:
        print(f"  {effect:<30} {prob}%")

print()
print("=" * 55)
print("TEST 2: Metformin + Lisinopril (generally safe combo)")
print("=" * 55)
for r in predict(['metformin'], 'lisinopril', age=50, gender='female'):
    if 'error' in r:
        print(f"Error: {r['error']}"); continue
    print(f"Pair         : {r['pair']}")
    print(f"Safety Score : {r['safety_score']}/100  [{r['risk_tier']}]")
    print(f"Side effects :")
    for effect, prob in r['side_effects']:
        print(f"  {effect:<30} {prob}%")

print()
print("=" * 55)
print("TEST 3: Multiple current drugs")
print("=" * 55)
for r in predict(['aspirin', 'lisinopril', 'atorvastatin'], 'ibuprofen'):
    if 'error' in r:
        print(f"Error: {r['error']}"); continue
    print(f"\nPair         : {r['pair']}")
    print(f"Safety Score : {r['safety_score']}/100  [{r['risk_tier']}]")
    print(f"Side effects : {[e for e, _ in r['side_effects'][:5]]}")