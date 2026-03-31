# 💊 MedSafeAI

> An AI-powered medication safety platform that predicts drug-drug interactions and adverse drug reactions using graph neural networks, molecular fingerprints, and large language models.

🌐 **Live Demo:** [medsafe-ai-alpha.vercel.app](https://medsafe-ai-alpha.vercel.app/)

---

## 📌 Overview

MedSafeAI is a full-stack clinical decision support tool built to help patients and caregivers make safer medication decisions. It offers two core capabilities:

- **Polypharmacy Interaction Checker** — Evaluates the safety of adding a new drug to a patient's existing medication list, returning a risk score, tier, and AI-generated explanation.
- **Adverse Drug Reaction (ADR) Predictor** — Predicts side effects for a single drug using a knowledge-graph-based model, grouped by body system category with confidence scores.

This project was developed as part of the S6 Mini Project — B.Tech Computer Science & Engineering.

---

## ✨ Features

| Feature | Description |
|---|---|
| ⚠️ Polypharmacy Interaction Check | Detects dangerous drug combinations from a patient's medication list |
| 🧬 ADR Side Effect Prediction | Predicts adverse reactions for a single drug by body system |
| 📊 Safety Scoring | Returns a 0–100 safety score with risk tiers: ✅ SAFE / ⚠️ CAUTION / 🚫 AVOID |
| 🤖 AI Explanations | Llama 3.3 70B (via Groq) generates plain-language clinical explanations |
| 🔍 Drug Search | Fuzzy search endpoints for both polypharmacy and ADR drug databases |
| 🖥️ Modern UI | React + Vite frontend with Tailwind CSS and Framer Motion animations |

---

## 🛠️ Tech Stack

### Frontend (`client/`)
| Technology | Version | Purpose |
|---|---|---|
| React | 19 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 8 | Build tool & dev server |
| Tailwind CSS | 4 | Styling |
| Framer Motion | 12 | Animations |
| Axios | 1.13 | API calls |
| React Router | 7 | Client-side routing |

### Backend (`server/`)
| Technology | Version | Purpose |
|---|---|---|
| FastAPI | 0.135 | REST API framework |
| Uvicorn | 0.41 | ASGI server |
| PyTorch | 2.10 | Deep learning inference |
| PyTorch Geometric | 2.7 | Graph neural networks |
| RDKit | 2025.9 | SMILES parsing & molecular fingerprints |
| Transformers (HuggingFace) | latest | BioBERT embeddings |
| Groq SDK | 0.28 | LLM API (Llama 3.3 70B) |
| Scikit-learn | 1.8 | ML utilities |
| SHAP | 0.51 | Model explainability |
| Pydantic | 2.12 | Request/response validation |

### Datasets
| Dataset | Usage |
|---|---|
| [TWOSIDES](http://tatonettilab.org/offsides/) | 42M FDA adverse event reports for polypharmacy training |
| [DrugBank](https://go.drugbank.com/) | Drug metadata, protein targets, known interactions |
| [SIDER](http://sideeffects.embl.de/) | Drug side effect database for ADR model training |
| [Reactome](https://reactome.org/) | Biological pathway data |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | SMILES molecular structures |

---

## 📁 Project Structure

```
S6-MiniProject/
├── client/                        # React + Vite frontend (TypeScript)
│   ├── public/
│   ├── src/
│   │   ├── api/                   # Axios API call functions
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/
│   │   │   ├── Landing.tsx        # Home / landing page
│   │   │   ├── PolypharmacyPredictor.tsx   # Drug interaction checker UI
│   │   │   └── ADRPredictor.tsx   # Side effect predictor UI
│   │   ├── types.ts               # TypeScript type definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── server/                        # FastAPI backend (Python)
    ├── api.py                     # Main FastAPI app & route definitions
    ├── schemas.py                 # Pydantic request/response models
    ├── requirements.txt
    ├── models/
    │   ├── poly_model.py          # MLP model for polypharmacy (TWOSIDES)
    │   └── adr_model.py          # BioBERT + HeteroGCN for ADR prediction
    ├── services/
    │   ├── poly_service.py        # Fingerprint generation, scoring, Groq AI
    │   └── adr_service.py        # ADR inference & Groq AI explanation
    ├── training_scripts/          # Offline model training code
    ├── best_model.pt             # Trained polypharmacy MLP weights
    ├── adr_model.pt              # Trained ADR HeteroGCN weights
    ├── fingerprint_dict.pkl      # Precomputed Morgan fingerprints (TWOSIDES drugs)
    ├── top_effects.pkl           # Top adverse effects labels
    └── adr_mappings.pkl         # Drug/SE/target/pathway index mappings
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js v18+
- Python 3.10+
- pip
- A [Groq API key](https://console.groq.com/) (free tier available)

---

### 1. Clone the Repository

```bash
git clone https://github.com/niranjanasiju/S6-MiniProject.git
cd S6-MiniProject
```

---

### 2. Backend Setup

```bash
cd server

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file and add your Groq API key:
# GROQ_API_KEY=your_key_here

# Start the FastAPI server
uvicorn api:app --reload --host 0.0.0.0 --port 8080
```

The API will be available at: `http://localhost:8080`  
Interactive API docs (Swagger UI): `http://localhost:8080/docs`

---

### 3. Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app will be available at: `http://localhost:5173`

---

## 📡 API Reference

### General

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |

### Polypharmacy Interaction Checker

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/drugs/search?q={query}` | Search polypharmacy drug database |
| `POST` | `/predict` | Check interaction safety for a drug combination |

**`POST /predict` — Example Request:**
```json
{
  "current_drugs": ["warfarin", "metformin"],
  "new_drug": "aspirin",
  "age": 65,
  "gender": "male"
}
```

**Response includes:** safety score (0–100), risk tier, predicted side effects per drug pair, and an AI-generated clinical explanation.

---

### ADR Predictor

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/adr/drugs/search?q={query}` | Search ADR drug database |
| `POST` | `/predict-adr` | Predict side effects for a single drug |

**`POST /predict-adr` — Example Request:**
```json
{
  "drug_name": "aspirin",
  "threshold": 0.5
}
```

**Response includes:** side effects by body system with confidence scores, biological protein targets, affected pathways, and an AI explanation.

---

### Risk Tiers

| Score | Tier | Meaning |
|---|---|---|
| ≥ 70 | ✅ `SAFE` | Low interaction risk |
| 45 – 69 | ⚠️ `CAUTION` | Moderate risk — consult a doctor |
| < 45 | 🚫 `AVOID` | High risk — potentially dangerous combination |

---

## 🔬 How It Works

### Polypharmacy Interaction Model

```
Drug A + Drug B (names)
        │
        ▼
Morgan Fingerprints (2048-dim, from fingerprint_dict.pkl)
        │
        ▼
Concatenated 4096-dim feature vector
        │
        ▼
MLP Classifier  ←  Trained on TWOSIDES (42M FDA adverse event reports)
        │
        ▼
Effect probabilities → Safety Score (0–100) + Risk Tier
        │
        ▼
Llama 3.3 70B via Groq → Plain-language clinical explanation
```

### ADR Prediction Model

```
Drug name → SMILES (PubChem) → BioBERT embeddings
        │
        ▼
Heterogeneous Knowledge Graph
  Nodes : Drug · Side Effect · Protein Target · Biological Pathway
  Edges : treats · targets · in_pathway · causes (+ reverses)
        │
        ▼
HeteroGCN  ←  Trained on SIDER + DrugBank + Reactome
        │
        ▼
Side effect predictions by body system + confidence scores
        │
        ▼
Llama 3.3 70B via Groq → Clinical AI explanation
```

---

## ⚠️ Disclaimer

MedSafeAI is an **academic research project** and is not intended for real clinical use. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider before making any medication decisions.

---

## 📄 License

This project is for academic purposes only. All rights reserved by the respective authors.
