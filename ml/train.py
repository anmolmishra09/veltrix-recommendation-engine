"""
Model training script for the recommendation platform.
Trains embedding and ranking models using interaction data.
"""
import os
import sys
import argparse
import logging
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from ml.features.user_features import get_user_feature_vector
from ml.features.product_features import get_product_feature_vector
from ml.recommendation.embeddings.model import EmbeddingModel
from ml.recommendation.ranking.model import RankingModel
from ml.utils.reproducibility import set_seed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InteractionDataset(Dataset):
    """
    Dataset for interaction data (user, product, label).
    Label: 1 for interaction (positive), 0 for non-interaction (negative).
    """
    def __init__(self, interactions_df: pd.DataFrame, num_negatives: int = 4):
        """
        Args:
            interactions_df: DataFrame with columns ['user_id', 'product_id', 'event_type']
            num_negatives: Number of negative samples per positive interaction
        """
        self.interactions = interactions_df.copy()
        self.num_negatives = num_negatives

        # Get unique users and items
        self.user_ids = self.interactions['user_id'].unique()
        self.product_ids = self.interactions['product_id'].unique()
        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(self.user_ids)}
        self.product_id_to_idx = {pid: idx for idx, pid in enumerate(self.product_ids)}
        self.num_users = len(self.user_ids)
        self.num_products = len(self.product_ids)

        # Build positive interactions (we'll treat any interaction as positive)
        self.positives = []
        for _, row in self.interactions.iterrows():
            uidx = self.user_id_to_idx[str(row['user_id'])]
            pidx = self.product_id_to_idx[str(row['product_id'])]
            self.positives.append((uidx, pidx, 1.0))  # label 1.0

        # Generate negative samples
        self.negatives = []
        for uidx, pidx, _ in self.positives:
            for _ in range(self.num_negatives):
                # Sample random product that the user has not interacted with
                neg_pidx = random.randint(0, self.num_products - 1)
                # Ensure it's not a positive interaction (simple check; could be improved)
                while (uidx, neg_pidx) in [(u, p) for u, p, _ in self.positives]:
                    neg_pidx = random.randint(0, self.num_products - 1)
                self.negatives.append((uidx, neg_pidx, 0.0))

        # Combine positives and negatives
        self.samples = self.positives + self.negatives
        random.shuffle(self.samples)
        logger.info(f"Created dataset with {len(self.positives)} positives and {len(self.negatives)} negatives")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        uidx, pidx, label = self.samples[idx]
        return torch.tensor(uidx, dtype=torch.long), torch.tensor(pidx, dtype=torch.long), torch.tensor(label, dtype=torch.float)

def train_embedding_model(
    interactions_df: pd.DataFrame,
    embedding_dim: int = 64,
    num_epochs: int = 10,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    model_output_path: str = "./models/embedding_model.pth"
):
    """
    Train the embedding model (two-tower dot product) on interaction data.
    """
    logger.info("Starting embedding model training...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Create dataset and dataloader
    dataset = InteractionDataset(interactions_df)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    model = EmbeddingModel(
        num_users=dataset.num_users,
        num_products=dataset.num_products,
        embedding_dim=embedding_dim
    ).to(device)

    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss()  # Works with raw logits
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0.0
        num_batches = 0
        for batch_idx, (user_idx, product_idx, labels) in enumerate(dataloader):
            user_idx = user_idx.to(device)
            product_idx = product_idx.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(user_idx, product_idx)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 100 == 0:
                logger.info(f"Epoch {epoch+1}/{num_epochs}, Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        logger.info(f"Epoch {epoch+1}/{num_epochs} completed. Average Loss: {avg_loss:.4f}")

    # Save model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    torch.save(model.state_dict(), model_output_path)
    logger.info(f"Embedding model saved to {model_output_path}")

    return model

def prepare_ranking_features(interactions_df: pd.DataFrame) -> tuple:
    """
    Prepare features for ranking model training.
    Returns (user_features, product_features, labels) as numpy arrays.
    """
    logger.info("Preparing features for ranking model...")
    # We'll create training instances from interactions (positive) and random non-interactions (negative)
    # For each interaction, we'll get user feature vector and product feature vector
    # Label = 1 for interaction, 0 for non-interaction

    # Get unique users and items
    user_ids = interactions_df['user_id'].unique()
    product_ids = interactions_df['product_id'].unique()

    positives = []
    for _, row in interactions_df.iterrows():
        uid = str(row['user_id'])
        pid = str(row['product_id'])
        try:
            u_feat = get_user_feature_vector(uid)
            p_feat = get_product_feature_vector(pid)
            positives.append((u_feat, p_feat, 1.0))
        except Exception as e:
            logger.warning(f"Could not get features for user {uid}, product {pid}: {e}")

    # Generate negatives
    negatives = []
    # We'll sample random user-item pairs that are not in interactions
    # Build a set of interacted pairs for quick lookup
    interacted_set = set(
        (str(row['user_id']), str(row['product_id'])) for _, row in interactions_df.iterrows()
    )
    # We'll generate up to len(positives) * 2 negatives
    max_negatives = len(positives) * 2
    tried = 0
    while len(negatives) < max_negatives and tried < max_negatives * 10:
        tried += 1
        uid = random.choice(user_ids)
        pid = random.choice(product_ids)
        if (uid, pid) in interacted_set:
            continue
        try:
            u_feat = get_user_feature_vector(uid)
            p_feat = get_product_feature_vector(pid)
            negatives.append((u_feat, p_feat, 0.0))
        except Exception as e:
            # Skip if feature extraction fails
            continue

    # Combine
    samples = positives + negatives
    random.shuffle(samples)
    logger.info(f"Prepared {len(positives)} positive and {len(negatives)} negative samples for ranking")

    # Separate features and labels
    user_feats = np.array([s[0] for s in samples], dtype=np.float32)
    product_feats = np.array([s[1] for s in samples], dtype=np.float32)
    labels = np.array([s[2] for s in samples], dtype=np.float32)

    return user_feats, product_feats, labels

def train_ranking_model(
    interactions_df: pd.DataFrame,
    user_feature_dim: int = 7,  # from user_features.py
    product_feature_dim: int = 7,  # from product_features.py
    hidden_dim: int = 128,
    num_epochs: int = 10,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    model_output_path: str = "./models/ranking_model.pth"
):
    """
    Train the ranking model (MLP) on user and product feature vectors.
    """
    logger.info("Starting ranking model training...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Prepare data
    user_feats, product_feats, labels = prepare_ranking_features(interactions_df)
    if len(user_feats) == 0:
        logger.error("No samples prepared for ranking model training")
        return None

    # Convert to tensors
    user_tensor = torch.from_numpy(user_feats).to(device)
    product_tensor = torch.from_numpy(product_feats).to(device)
    labels_tensor = torch.from_numpy(labels).to(device)

    # Create dataset and dataloader
    dataset = torch.utils.data.TensorDataset(user_tensor, product_tensor, labels_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    model = RankingModel(
        user_feature_dim=user_feature_dim,
        product_feature_dim=product_feature_dim,
        hidden_dim=hidden_dim
    ).to(device)

    # Loss and optimizer
    criterion = nn.BCELoss()  # Since model outputs sigmoid
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0.0
        num_batches = 0
        for batch_idx, (u_batch, p_batch, l_batch) in enumerate(dataloader):
            optimizer.zero_grad()
            outputs = model(u_batch, p_batch)
            loss = criterion(outputs, l_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 100 == 0:
                logger.info(f"Epoch {epoch+1}/{num_epochs}, Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        logger.info(f"Epoch {epoch+1}/{num_epochs} completed. Average Loss: {avg_loss:.4f}")

    # Save model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    torch.save(model.state_dict(), model_output_path)
    logger.info(f"Ranking model saved to {model_output_path}")

    return model

def main():
    parser = argparse.ArgumentParser(description='Train recommendation models')
    parser.add_argument('--data-dir', type=str, default='.', help='Directory containing interactions.csv')
    parser.add_argument('--embedding-dim', type=int, default=64, help='Embedding dimension')
    parser.add_argument('--ranking-hidden-dim', type=int, default=128, help='Hidden dimension for ranking model')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=512, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--model-output-dir', type=str, default='./models', help='Directory to save models')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # Set seed for reproducibility
    set_seed(args.seed)

    # Load interactions data
    interactions_path = os.path.join(args.data_dir, 'interactions.csv')
    if not os.path.exists(interactions_path):
        logger.error(f"Interactions file not found at {interactions_path}")
        sys.exit(1)

    logger.info(f"Loading interactions from {interactions_path}")
    interactions_df = pd.read_csv(interactions_path)
    logger.info(f"Loaded {len(interactions_df)} interactions")

    # Ensure required columns exist
    required_cols = ['user_id', 'product_id', 'event_type']
    if not all(col in interactions_df.columns for col in required_cols):
        logger.error(f"Interactions file must contain columns: {required_cols}")
        sys.exit(1)

    # Train embedding model
    embedding_model_path = os.path.join(args.model_output_dir, 'embedding_model.pth')
    train_embedding_model(
        interactions_df=interactions_df,
        embedding_dim=args.embedding_dim,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        model_output_path=embedding_model_path
    )

    # Train ranking model
    ranking_model_path = os.path.join(args.model_output_dir, 'ranking_model.pth')
    train_ranking_model(
        interactions_df=interactions_df,
        user_feature_dim=7,  # Hardcoded from user_features.py
        product_feature_dim=7,  # Hardcoded from product_features.py
        hidden_dim=args.ranking_hidden_dim,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        model_output_path=ranking_model_path
    )

    logger.info("Training completed successfully!")

if __name__ == "__main__":
    main()