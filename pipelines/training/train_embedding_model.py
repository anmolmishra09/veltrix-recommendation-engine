"""
Training script for the embedding model.
"""
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from ml.recommendation.embeddings.model import EmbeddingModel
import numpy as np

class InteractionDataset(Dataset):
    def __init__(self, interactions_df, num_users, num_products):
        self.users = interactions_df['user_id'].values
        self.products = interactions_df['product_id'].values
        # For implicit feedback, we can use 1 for interaction (view, click, purchase) and weight by type
        self.weights = interactions_df['weight'].values  # We'll assign weights: view=1, click=2, purchase=3

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        user_idx = self.users[idx]
        product_idx = self.products[idx]
        # weight = self.weights[idx]
        return torch.LongTensor([user_idx]), torch.LongTensor([product_idx])  # , torch.FloatTensor([weight])

def main():
    # Load interactions (we need to generate this from events)
    # For now, we'll create a dummy dataset
    interactions_df = pd.DataFrame({
        'user_id': np.random.randint(0, 1000, size=10000),
        'product_id': np.random.randint(0, 100, size=10000),
        # 'weight': np.random.choice([1, 2, 3], size=10000)  # view, click, purchase
    })

    num_users = interactions_df['user_id'].nunique()
    num_products = interactions_df['product_id'].nunique()

    dataset = InteractionDataset(interactions_df, num_users, num_products)
    dataloader = DataLoader(dataset, batch_size=256, shuffle=True)

    model = EmbeddingModel(num_users, num_products, embedding_dim=64)
    criterion = nn.BCELoss()  # We'll treat as binary classification: interaction or not
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    num_epochs = 10
    for epoch in range(num_epochs):
        total_loss = 0
        for batch_users, batch_products in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_users, batch_products)
            # We need labels: for now, we'll use all ones (positive samples) and sample negative samples
            # For simplicity, we'll skip negative sampling and just use positive samples with BCELoss and target=1
            labels = torch.ones_like(outputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f'Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(dataloader):.4f}')

    # Save the model
    torch.save(model.state_dict(), './models/embedding_model.pth')

if __name__ == '__main__':
    main()