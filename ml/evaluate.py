"""
Model evaluation script for the recommendation platform.
Evaluates embedding and ranking models on test data.
"""
import argparse
import json
import logging
import os
import random
import sys
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, TensorDataset

from ml.features.product_features import get_product_feature_vector
from ml.features.user_features import get_user_feature_vector
from ml.recommendation.embeddings.model import EmbeddingModel
from ml.recommendation.ranking.model import RankingModel
from ml.utils.reproducibility import set_seed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InteractionDataset(Dataset):
    """
    Dataset for interaction data (user, product, label).
    """
    def __init__(self, interactions_df: pd.DataFrame, num_negatives: int = 4):
        self.interactions = interactions_df.copy()
        self.num_negatives = num_negatives

        self.user_ids = self.interactions['user_id'].unique()
        self.product_ids = self.interactions['product_id'].unique()
        self.user_id_to_idx = {str(uid): idx for idx, uid in enumerate(self.user_ids)}
        self.product_id_to_idx = {str(pid): idx for idx, pid in enumerate(self.product_ids)}
        self.num_users = len(self.user_ids)
        self.num_products = len(self.product_ids)

        self.positives = []
        positive_pairs = set()
        for _, row in self.interactions.iterrows():
            uidx = self.user_id_to_idx[str(row['user_id'])]
            pidx = self.product_id_to_idx[str(row['product_id'])]
            self.positives.append((uidx, pidx, 1.0))
            positive_pairs.add((uidx, pidx))

        self.negatives = []
        for uidx, pidx, _ in self.positives:
            for _ in range(self.num_negatives):
                neg_pidx = random.randint(0, self.num_products - 1)
                attempts = 0
                while (uidx, neg_pidx) in positive_pairs and attempts < 100:
                    neg_pidx = random.randint(0, self.num_products - 1)
                    attempts += 1
                self.negatives.append((uidx, neg_pidx, 0.0))

        self.samples = self.positives + self.negatives
        random.shuffle(self.samples)
        logger.info(
            f"Created evaluation dataset with {len(self.positives)} positives and {len(self.negatives)} negatives"
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        uidx, pidx, label = self.samples[idx]
        return (
            torch.tensor(uidx, dtype=torch.long),
            torch.tensor(pidx, dtype=torch.long),
            torch.tensor(label, dtype=torch.float),
        )


def evaluate_embedding_model(
    model: EmbeddingModel,
    interactions_df: pd.DataFrame,
    num_negatives: int = 4,
    batch_size: int = 512,
) -> Dict[str, float]:
    """
    Evaluate the embedding model using AUC, accuracy, etc.
    """
    logger.info("Evaluating embedding model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    dataset = InteractionDataset(interactions_df, num_negatives=num_negatives)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_labels = []
    all_probs = []

    with torch.no_grad():
        for user_idx, product_idx, labels in dataloader:
            user_idx = user_idx.to(device)
            product_idx = product_idx.to(device)
            labels = labels.to(device)

            logits = model(user_idx, product_idx)
            probs = torch.sigmoid(logits)

            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    all_preds = (all_probs >= 0.5).astype(int)

    try:
        auc = roc_auc_score(all_labels, all_probs)
    except Exception as e:
        logger.warning(f"Could not compute AUC: {e}")
        auc = 0.5

    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='binary', zero_division=0
    )

    metrics = {
        "auc": float(auc),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }

    logger.info(f"Embedding model evaluation metrics: {metrics}")
    return metrics


def evaluate_ranking_model(
    model: RankingModel,
    interactions_df: pd.DataFrame,
    batch_size: int = 512,
) -> Dict[str, float]:
    """
    Evaluate the ranking model.
    Predicts probability of interaction given user and product features.
    """
    logger.info("Evaluating ranking model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

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
            logger.warning(f"Skipping row due to feature error: {e}")

    negatives = []
    interacted_set = {
        (str(row['user_id']), str(row['product_id']))
        for _, row in interactions_df.iterrows()
    }
    max_negatives = len(positives) * 2
    tried = 0
    while len(negatives) < max_negatives and tried < max_negatives * 10:
        tried += 1
        uid = str(random.choice(user_ids))
        pid = str(random.choice(product_ids))
        if (uid, pid) in interacted_set:
            continue
        try:
            u_feat = get_user_feature_vector(uid)
            p_feat = get_product_feature_vector(pid)
            negatives.append((u_feat, p_feat, 0.0))
        except Exception:
            continue

    samples = positives + negatives
    random.shuffle(samples)
    logger.info(f"Evaluation ranking set: {len(positives)} positives, {len(negatives)} negatives")

    if not samples:
        logger.error("No samples for ranking evaluation")
        return {"auc": 0.5, "accuracy": 0.5, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    user_feats = np.array([s[0] for s in samples], dtype=np.float32)
    product_feats = np.array([s[1] for s in samples], dtype=np.float32)
    labels = np.array([s[2] for s in samples], dtype=np.float32)

    user_tensor = torch.from_numpy(user_feats).to(device)
    product_tensor = torch.from_numpy(product_feats).to(device)
    labels_tensor = torch.from_numpy(labels).to(device)

    dataset = TensorDataset(user_tensor, product_tensor, labels_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_labels = []
    all_probs = []

    with torch.no_grad():
        for u_batch, p_batch, l_batch in dataloader:
            u_batch = u_batch.to(device)
            p_batch = p_batch.to(device)
            l_batch = l_batch.to(device)

            probs = model(u_batch, p_batch)
            all_labels.extend(l_batch.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    all_preds = (all_probs >= 0.5).astype(int)

    try:
        auc = roc_auc_score(all_labels, all_probs)
    except Exception as e:
        logger.warning(f"Could not compute AUC: {e}")
        auc = 0.5

    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='binary', zero_division=0
    )

    metrics = {
        "auc": float(auc),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }

    logger.info(f"Ranking model evaluation metrics: {metrics}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Evaluate recommendation models')
    parser.add_argument('--data-dir', type=str, default='.', help='Directory containing interactions.csv')
    parser.add_argument('--model-dir', type=str, default='./models', help='Directory containing trained models')
    parser.add_argument('--batch-size', type=int, default=512, help='Batch size for evaluation')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    set_seed(args.seed)

    interactions_path = os.path.join(args.data_dir, 'interactions.csv')
    if not os.path.exists(interactions_path):
        logger.error(f"Interactions file not found at {interactions_path}")
        sys.exit(1)

    logger.info(f"Loading interactions from {interactions_path}")
    interactions_df = pd.read_csv(interactions_path)
    logger.info(f"Loaded {len(interactions_df)} interactions")

    embedding_model_path = os.path.join(args.model_dir, 'embedding_model.pth')
    if not os.path.exists(embedding_model_path):
        logger.error(f"Embedding model not found at {embedding_model_path}")
        sys.exit(1)

    embedding_model = EmbeddingModel(num_users=1000, num_products=100, embedding_dim=64)
    embedding_model.load_state_dict(torch.load(embedding_model_path, map_location='cpu'))
    logger.info(f"Loaded embedding model from {embedding_model_path}")

    ranking_model_path = os.path.join(args.model_dir, 'ranking_model.pth')
    if not os.path.exists(ranking_model_path):
        logger.error(f"Ranking model not found at {ranking_model_path}")
        sys.exit(1)

    try:
        sample_user_feat = get_user_feature_vector("1")
        sample_product_feat = get_product_feature_vector("1")
        user_feature_dim = len(sample_user_feat)
        product_feature_dim = len(sample_product_feat)
    except Exception as e:
        logger.warning(f"Could not infer feature dimensions, using defaults: {e}")
        user_feature_dim = 7
        product_feature_dim = 7

    ranking_model = RankingModel(
        user_feature_dim=user_feature_dim,
        product_feature_dim=product_feature_dim,
        hidden_dim=128
    )
    ranking_model.load_state_dict(torch.load(ranking_model_path, map_location='cpu'))
    logger.info(f"Loaded ranking model from {ranking_model_path}")

    emb_metrics = evaluate_embedding_model(
        model=embedding_model,
        interactions_df=interactions_df,
        batch_size=args.batch_size
    )

    rank_metrics = evaluate_ranking_model(
        model=ranking_model,
        interactions_df=interactions_df,
        batch_size=args.batch_size
    )

    print("\n=== Embedding Model Evaluation ===")
    for k, v in emb_metrics.items():
        print(f"{k}: {v:.4f}")

    print("\n=== Ranking Model Evaluation ===")
    for k, v in rank_metrics.items():
        print(f"{k}: {v:.4f}")

    os.makedirs(args.model_dir, exist_ok=True)
    metrics_file = os.path.join(args.model_dir, 'evaluation_metrics.json')
    metrics = {
        "embedding": emb_metrics,
        "ranking": rank_metrics
    }
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Evaluation metrics saved to {metrics_file}")


if __name__ == "__main__":
    main()