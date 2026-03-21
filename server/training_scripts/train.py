import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from sklearn.preprocessing import StandardScaler
import pickle

# ── Load data ─────────────────────────────────────────────────────────
X = np.load('X.npy')
Y = np.load('Y.npy')
scores = np.load('scores.npy')

print(f"X: {X.shape}, Y: {Y.shape}, scores: {scores.shape}")

# ── Normalize scores to 0-1 for training ─────────────────────────────
scores_norm = scores / 100.0

# ── Convert to tensors ────────────────────────────────────────────────
X_tensor = torch.tensor(X, dtype=torch.float32)
Y_tensor = torch.tensor(Y, dtype=torch.float32)
S_tensor = torch.tensor(scores_norm, dtype=torch.float32).unsqueeze(1)

dataset = TensorDataset(X_tensor, Y_tensor, S_tensor)

# 80/20 train/val split
train_size = int(0.8 * len(dataset))
val_size   = len(dataset) - train_size
train_ds, val_ds = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
val_loader   = DataLoader(val_ds,   batch_size=256)

print(f"Train pairs: {train_size}, Val pairs: {val_size}")

# ── Model ─────────────────────────────────────────────────────────────
class DrugInteractionModel(nn.Module):
    def __init__(self, input_dim=4096, hidden_dim=512, num_effects=50):
        super().__init__()

        # Shared backbone
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

        # Head 1: side effect prediction (multi-label)
        self.effect_head = nn.Sequential(
            nn.Linear(128, num_effects),
            nn.Sigmoid()            # each effect independently 0-1
        )

        # Head 2: safety score (regression)
        self.score_head = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()            # output 0-1 (we'll multiply by 100)
        )

    def forward(self, x):
        features = self.backbone(x)
        effects  = self.effect_head(features)
        score    = self.score_head(features)
        return effects, score

model = DrugInteractionModel()
print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")

# ── Training setup ────────────────────────────────────────────────────
optimizer     = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler     = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
effect_loss_fn = nn.BCELoss()
score_loss_fn  = nn.MSELoss()

# ── Training loop ─────────────────────────────────────────────────────
EPOCHS = 40
best_val_loss = float('inf')

print("\nTraining...\n")
print(f"{'Epoch':>6} {'Train Loss':>12} {'Val Loss':>10} {'Val Acc':>10}")
print("-" * 44)

for epoch in range(1, EPOCHS + 1):

    # Train
    model.train()
    train_loss = 0
    for xb, yb, sb in train_loader:
        optimizer.zero_grad()
        pred_effects, pred_score = model(xb)
        loss = effect_loss_fn(pred_effects, yb) + 0.5 * score_loss_fn(pred_score, sb)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    train_loss /= len(train_loader)

    # Validate
    model.eval()
    val_loss, correct, total = 0, 0, 0
    with torch.no_grad():
        for xb, yb, sb in val_loader:
            pred_effects, pred_score = model(xb)
            loss = effect_loss_fn(pred_effects, yb) + 0.5 * score_loss_fn(pred_score, sb)
            val_loss += loss.item()

            # Accuracy: predicted label matches true label (threshold 0.5)
            preds = (pred_effects > 0.5).float()
            correct += (preds == yb).sum().item()
            total   += yb.numel()

    val_loss /= len(val_loader)
    val_acc   = 100 * correct / total

    scheduler.step(val_loss)

    # Save best model
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), 'best_model.pt')

    if epoch % 5 == 0:
        print(f"{epoch:>6} {train_loss:>12.4f} {val_loss:>10.4f} {val_acc:>9.1f}%")

print(f"\nBest val loss: {best_val_loss:.4f}")
print("Model saved to best_model.pt")

# ── Save side effects list for inference later ────────────────────────
with open('top_effects.pkl', 'rb') as f:
    top_effects = pickle.load(f)
print(f"Side effects list: {top_effects[:5]}...")
print("\nTraining complete!")