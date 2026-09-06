"""
Ranking model to score candidate products for a user.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

class RankingModel(nn.Module):
    def __init__(self, user_feature_dim, product_feature_dim, hidden_dim=128):
        super(RankingModel, self).__init__()
        self.user_fc = nn.Linear(user_feature_dim, hidden_dim)
        self.product_fc = nn.Linear(product_feature_dim, hidden_dim)
        self.combined_fc = nn.Linear(hidden_dim * 2, hidden_dim)
        self.output_fc = nn.Linear(hidden_dim, 1)

    def forward(self, user_features, product_features):
        user_out = F.relu(self.user_fc(user_features))
        product_out = F.relu(self.product_fc(product_features))
        combined = torch.cat([user_out, product_out], dim=1)
        combined_out = F.relu(self.combined_fc(combined))
        output = torch.sigmoid(self.output_fc(combined_out))
        return output.squeeze(-1)