import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger
import pickle

# Suppress RDKit warnings for invalid SMILES
RDLogger.DisableLog('rdApp.*')

def smiles_to_fingerprint(smiles, radius=2, n_bits=2048):
    """Convert a SMILES string to a Morgan fingerprint vector"""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=radius, nBits=n_bits)
        return np.array(fp)
    except Exception:
        return None

# ── Load dataset ─────────────────────────────────────────────────────
df = pd.read_csv('drugbank_processed.csv', encoding='latin-1')
df['name'] = df['name'].str.lower().str.strip()
df = df[['name', 'smiles']].dropna().drop_duplicates(subset='name')

print(f"Processing {len(df)} drugs...")

# ── Generate fingerprints ─────────────────────────────────────────────
fingerprint_dict = {}
failed = []

for _, row in df.iterrows():
    fp = smiles_to_fingerprint(row['smiles'])
    if fp is not None:
        fingerprint_dict[row['name']] = fp
    else:
        failed.append(row['name'])

print(f"\nSuccessfully fingerprinted : {len(fingerprint_dict)}")
print(f"Failed (invalid SMILES)    : {len(failed)}")
if failed:
    print(f"Sample failures: {failed[:5]}")

# ── Save to disk ──────────────────────────────────────────────────────
with open('fingerprint_dict.pkl', 'wb') as f:
    pickle.dump(fingerprint_dict, f)

print("\nSaved to fingerprint_dict.pkl")

# ── Quick sanity check ────────────────────────────────────────────────
sample_drug = 'aspirin'
if sample_drug in fingerprint_dict:
    fp = fingerprint_dict[sample_drug]
    print(f"\nAspirin fingerprint shape : {fp.shape}")
    print(f"Non-zero bits             : {fp.sum()} / 2048")
    print(f"First 20 bits             : {fp[:20]}")

