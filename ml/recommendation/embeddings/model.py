"""
Embedding model for learning product and user embeddings from interactions.
"""
import numpy as np
import torch
import torch.nn as nn

class EmbeddingModel(nn.Module):
    def __init__(self, num_users, num_products, embedding_dim=64):
        super(EmbeddingModel, self).__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.product_embedding = nn.Embedding(num_products, embedding_dim)

    def forward(self, user_indices, product_indices):
        user_embedded = self.user_embedding(user_indices)
        product_embedded = self.product_embedding(product_indices)
        return torch.sum(user_embedded * product_embedded, dim=1)

    def get_user_embedding(self, user_indices):
        return self.user_embedding(user_indices)

    def get_product_embedding(self, product_indices):
        return self.product_embedding(product_indices)