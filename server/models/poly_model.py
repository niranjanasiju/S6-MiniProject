import torch
import torch.nn as nn


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
        self.effect_head = nn.Sequential(nn.Linear(128, num_effects), nn.Sigmoid())
        self.score_head  = nn.Sequential(nn.Linear(128, 32), nn.ReLU(),
                                          nn.Linear(32, 1), nn.Sigmoid())

    def forward(self, x):
        features = self.backbone(x)
        return self.effect_head(features), self.score_head(features)


def load_poly_model(weights_path: str = 'best_model.pt') -> DrugInteractionModel:
    model = DrugInteractionModel()
    model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    print("Polypharmacy model loaded!")
    return model