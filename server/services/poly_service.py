import numpy as np
import torch
import requests
from rdkit import Chem
from rdkit.Chem import AllChem
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


def get_fingerprint(drug_name: str, fp_dict: dict) -> np.ndarray | None:
    key = drug_name.lower().strip()
    key = DRUG_ALIASES.get(key, key)
    if key in fp_dict:
        return fp_dict[key]
    url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug"
           f"/compound/name/{requests.utils.quote(key)}"
           f"/property/IsomericSMILES/JSON")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            smiles = r.json()['PropertyTable']['Properties'][0]['IsomericSMILES']
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                fp  = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
                arr = np.array(fp, dtype=np.float32)
                fp_dict[key] = arr
                return arr
    except Exception:
        pass
    return None


def compute_safety_score(effect_probs, top_effects: list, threshold: float = 0.25):
    risk, detected = 0, []
    for i, effect in enumerate(top_effects):
        prob = float(effect_probs[i])
        if prob > threshold:
            weight = SEVERITY_WEIGHTS.get(effect, 2)
            risk  += prob * weight
            detected.append({'effect': effect,
                              'probability': round(prob * 100, 1),
                              'severity': weight})
    safety = round(max(0, min(100, 100 - (risk / 5) * 100)), 1)
    tier   = "SAFE" if safety >= 70 else ("CAUTION" if safety >= 45 else "AVOID")
    return safety, tier, sorted(detected, key=lambda x: -x['probability'])


def get_ai_explanation(new_drug, existing_drug, side_effects,
                        safety_score, risk_tier, age, gender) -> str:
    effects_text = (", ".join([e['effect'] for e in side_effects])
                    if side_effects else "no significant side effects detected")
    prompt = f"""You are a helpful medical assistant explaining drug interactions to a patient 
in simple, clear language. Be empathetic and avoid medical jargon. 
Never tell the patient to ignore their doctor's advice.

A {age}-year-old {gender} is currently taking {existing_drug} and wants to add {new_drug}.

Our ML model analysis found:
- Safety score: {safety_score}/100
- Risk level: {risk_tier}
- Predicted side effects: {effects_text}

Provide a response with exactly these 5 sections:

**What is {new_drug}?**
(1-2 sentences — what is this drug commonly prescribed for?)

**What did we find?**
(Explain the safety score and risk level in plain English — what does this mean 
for the patient in practical terms?)

**Side effects to watch for:**
(Explain each predicted side effect in simple everyday language a non-medical 
person would understand. If none, reassure the patient warmly.)

**Safe usage tips:**
(General awareness about dosage and timing for a {age}-year-old {gender}. 
Always note that exact dosage must be confirmed with their doctor.)

**When to call your doctor:**
(Specific warning signs they should not ignore, based on the predicted side effects.)

Keep the entire response under 300 words. Use simple everyday language.
Write as if talking to a worried patient, not a medical professional."""
    try:
        response = groq_client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI explanation unavailable: {str(e)}"