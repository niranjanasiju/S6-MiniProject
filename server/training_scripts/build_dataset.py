import pandas as pd
import numpy as np
import pickle

print("Loading TWOSIDES in chunks (4 columns only)...")
chunks = []
for chunk in pd.read_csv('TWOSIDES.csv', low_memory=False, chunksize=500_000,
                          usecols=['drug_1_concept_name', 'drug_2_concept_name',
                                   'condition_concept_name', 'mean_reporting_frequency']):
    chunk['drug_1_concept_name']   = chunk['drug_1_concept_name'].str.lower().str.strip()
    chunk['drug_2_concept_name']   = chunk['drug_2_concept_name'].str.lower().str.strip()
    chunk['condition_concept_name'] = chunk['condition_concept_name'].str.lower().str.strip()
    chunk['mean_reporting_frequency'] = pd.to_numeric(
        chunk['mean_reporting_frequency'], errors='coerce').fillna(0.0)
    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)
print(f"Total rows: {len(df):,}")

print("Loading fingerprints...")
with open('fingerprint_dict.pkl', 'rb') as f:
    fp_dict = pickle.load(f)

mask = (
    df['drug_1_concept_name'].isin(fp_dict) &
    df['drug_2_concept_name'].isin(fp_dict)
)
df = df[mask].copy()
print(f"Rows after fingerprint filter: {len(df):,}")

df = df[df['mean_reporting_frequency'] > 0.1].copy()
print(f"Rows after frequency filter (>10%): {len(df):,}")

top_effects = (
    df['condition_concept_name']
    .value_counts()
    .head(50)
    .index.tolist()
)
print(f"\nTop 10 side effects (significant only):")
for e in top_effects[:10]:
    print(f"  {e}")

df_top = df[df['condition_concept_name'].isin(top_effects)]

print("\nBuilding drug pair dataset...")
grouped = df_top.groupby(['drug_1_concept_name', 'drug_2_concept_name'])

X_list, Y_list, score_list = [], [], []

for (drug1, drug2), group in grouped:
    fp1 = fp_dict[drug1]
    fp2 = fp_dict[drug2]
    x   = np.concatenate([fp1, fp2])

    effects_present = set(group['condition_concept_name'].tolist())
    y = np.array([1 if e in effects_present else 0 for e in top_effects],
                 dtype=np.float32)

    # ── UPDATED safety score formula ──────────────────────────────────
    max_freq          = group['mean_reporting_frequency'].max()
    avg_freq          = group['mean_reporting_frequency'].mean()
    num_effects       = len(effects_present)
    high_freq_count   = (group['mean_reporting_frequency'] > 0.3).sum()
    medium_freq_count = (group['mean_reporting_frequency'] > 0.2).sum()

    severity = (
        max_freq          * 60 +
        avg_freq          * 25 +
        high_freq_count   *  8 +
        medium_freq_count *  3
    )
    severity     = min(severity, 100)
    safety_score = round(100 - severity, 2)
    # ─────────────────────────────────────────────────────────────────

    X_list.append(x)
    Y_list.append(y)
    score_list.append(safety_score)

X      = np.array(X_list,  dtype=np.float32)
Y      = np.array(Y_list,  dtype=np.float32)
scores = np.array(score_list, dtype=np.float32)

print(f"\nDataset shape:")
print(f"  X : {X.shape}")
print(f"  Y : {Y.shape}")
print(f"  scores : {scores.shape}")
print(f"Safety score range : {scores.min():.1f} → {scores.max():.1f}")
print(f"Avg side effects per pair : {Y.sum(axis=1).mean():.2f}")
print(f"Pairs with 0 effects : {(Y.sum(axis=1) == 0).sum()}")
print(f"Pairs with >10 effects : {(Y.sum(axis=1) > 10).sum()}")

np.save('X.npy', X)
np.save('Y.npy', Y)
np.save('scores.npy', scores)

with open('top_effects.pkl', 'wb') as f:
    pickle.dump(top_effects, f)

print("\nSaved! Dataset ready for training.")