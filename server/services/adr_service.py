import torch
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def predict_adr(drug_name, adr_model, adr_hdata,
                adr_drug2idx, adr_idx2se,
                SIDE_EFFECT_CATEGORIES, N_ADR_SE,
                threshold: float = 0.5):
    drug_idx = torch.tensor([adr_drug2idx[drug_name]], dtype=torch.long)
    with torch.no_grad():
        logits = adr_model(drug_idx, [drug_name], adr_hdata)
        probs  = torch.sigmoid(logits).cpu().numpy()[0]

    predicted = [
        {'effect': adr_idx2se[i],
         'probability': round(float(probs[i]) * 100, 1),
         'category': SIDE_EFFECT_CATEGORIES.get(adr_idx2se[i], 'Other')}
        for i in range(N_ADR_SE) if probs[i] >= threshold
    ]
    return sorted(predicted, key=lambda x: -x['probability'])


def get_adr_ai_explanation(drug_name, side_effects, targets, pathways) -> str:
    effects_text = (", ".join([e['effect'] for e in side_effects[:10]])
                    if side_effects else "no significant side effects predicted")
    prompt = f"""You are a helpful medical assistant explaining drug side effects to a patient
in simple, clear language. Be empathetic and avoid medical jargon.

Our AI model analyzed the drug {drug_name} and predicted the following side effects:
{effects_text}

The drug works on these biological targets: {', '.join(targets[:5]) if targets else 'unknown'}

Provide a brief, friendly explanation with these 3 sections:

**What is {drug_name}?**
(1-2 sentences on what this drug is commonly used for.)

**Possible side effects:**
(Explain the top predicted side effects in plain, everyday language.)

**What to watch for:**
(Key warning signs a patient should not ignore.)

Keep the entire response under 200 words. Write as if talking to a worried patient."""
    try:
        response = groq_client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 400,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI explanation unavailable: {str(e)}"