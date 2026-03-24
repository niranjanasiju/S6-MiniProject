import torch
from groq import Groq
import os
from dotenv import load_dotenv
import json
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ================================
# SMILES → Fingerprint
# ================================
def smiles_to_fp(smiles):
    if not smiles:
        return torch.zeros((1, 2048))

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return torch.zeros((1, 2048))

    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
    arr = np.zeros((2048,))
    DataStructs.ConvertToNumpyArray(fp, arr)

    return torch.tensor(arr, dtype=torch.float32).unsqueeze(0)

# ================================
# MAIN PREDICTION FUNCTION
# ================================
def predict_adr(
    drug_name,
    adr_model,
    adr_hdata,
    adr_drug2idx,
    adr_idx2se,
    DRUG_SMILES,
    SIDE_EFFECT_CATEGORIES,
    N_ADR_SE,
    threshold=0.3
):
    norm = drug_name.lower().strip()

    # ================================
    # 1. Resolve SMILES
    # ================================
    smiles = DRUG_SMILES.get(norm)

    if smiles is None:
        print(f"⚠️ '{norm}' not in SMILES database → using zero fingerprint")
        fp = torch.zeros((1, 2048))
    else:
        fp = smiles_to_fp(smiles)

    device = next(adr_model.parameters()).device
    fp = fp.to(device)

    # ================================
    # 2. Handle known vs unknown drug
    # ================================
    is_known = norm in adr_drug2idx

    if is_known:
        drug_idx_val = adr_drug2idx[norm]
    else:
        print(f"⚠️ '{norm}' NOT in training set → using fallback drug")

        # 🔥 Simple fallback (safe for demo)
        drug_idx_val = list(adr_drug2idx.values())[0]

    drug_idx = torch.tensor([drug_idx_val], dtype=torch.long).to(device)

    # ================================
    # 3. Forward pass
    # ================================
    with torch.no_grad():
        logits = adr_model(drug_idx, [norm], adr_hdata, fp)
        probs = torch.sigmoid(logits).cpu().numpy()[0]

    # ================================
    # 4. Format results
    # ================================
    predicted = [
        {
            "effect": adr_idx2se[i],
            "probability": round(float(probs[i]) * 100, 1),
            "category": SIDE_EFFECT_CATEGORIES.get(adr_idx2se[i], "Other")
        }
        for i in range(N_ADR_SE)
        if probs[i] >= threshold
    ]

    predicted = sorted(predicted, key=lambda x: -x["probability"])[:10]

    return {
        "drug": norm,
        "is_known": is_known,
        "side_effects": predicted
    }

# ================================
# AI EXPLANATION (UNCHANGED)
# ================================
def get_adr_ai_explanation(drug_name, side_effects, targets, pathways) -> dict:
    effects_text = (
        ", ".join([e['effect'] for e in side_effects[:10]])
        if side_effects else "no significant side effects predicted"
    )

    prompt = f"""You are a helpful medical assistant explaining drug side effects to a patient
in simple, clear language. Be empathetic and avoid medical jargon.
Never tell the patient to ignore their doctor's advice.

Our AI model analyzed the drug {drug_name} and predicted the following side effects:
{effects_text}

The drug works on these biological targets: {', '.join(targets[:5]) if targets else 'unknown'}

Return your response ONLY as a JSON object matching exactly this schema:
{{
  "what_is_it": "1-2 sentences on what {drug_name} is commonly used for.",
  "what_did_we_find": "Explain the predicted side effect profile in plain English — what does this mean for the patient in practical terms?",
  "side_effects_to_watch": "Explain the top predicted side effects in plain, everyday language.",
  "safe_usage_tips": "General awareness about dosage and timing. Always note that exact dosage must be confirmed with their doctor.",
  "when_to_call_doctor": "Key warning signs a patient should not ignore based on these side effects."
}}

Keep each section concise. Write as if talking to a worried patient.
Output ONLY valid JSON."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {
            "what_is_it": f"AI explanation unavailable: {str(e)}",
            "what_did_we_find": "",
            "side_effects_to_watch": "",
            "safe_usage_tips": "",
            "when_to_call_doctor": ""
        }