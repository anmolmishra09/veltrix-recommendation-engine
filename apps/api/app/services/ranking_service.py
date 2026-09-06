"""
Ranking service for scoring candidate items.
"""
import torch
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from ..core.config import settings
from ..core.model_loader import ModelLoader
import logging

logger = logging.getLogger(__name__)

class RankingService:
    def __init__(self):
        self.logger = logger
        self.model_loader = ModelLoader()
        self.ranking_model = self.model_loader.get_ranking_model()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ranking_model.to(self.device)
        self.ranking_model.eval()
        self.logger.info(f"Ranking service initialized on {self.device}")

    def score_candidates(
        self,
        user_features: np.ndarray,
        product_features_list: List[np.ndarray]
    ) -> List[float]:
        """
        Score a list of product candidates for a given user.
        """
        if not product_features_list:
            return []

        try:
            # Convert to tensors
            user_tensor = torch.from_numpy(user_features).float().to(self.device)
            # Stack product features
            product_tensor = torch.from_numpy(np.stack(product_features_list)).float().to(self.device)

            # Batch the user features for each candidate
            user_batch = user_tensor.repeat(len(product_features_list), 1)

            with torch.no_grad():
                scores = self.ranking_model(user_batch, product_tensor)
                scores = scores.cpu().numpy().flatten()

            return scores.tolist()
        except Exception as e:
            self.logger.error(f"Error scoring candidates: {e}")
            # Return zero scores as fallback
            return [0.0] * len(product_features_list)

    def score_candidates_from_dicts(
        self,
        user_feature_dict: Dict[str, Any],
        product_feature_dicts: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Score candidates from dictionaries of features.
        In a real implementation, we would convert dicts to arrays.
        For now, we'll return dummy scores.
        """
        self.logger.warning("Using dummy ranking service - feature dict conversion not implemented")
        return [0.5] * len(product_feature_dicts)

    def get_user_feature_vector(self, user_id: str, feature_store) -> np.ndarray:
        """
        Get user feature vector from feature store.
        Placeholder implementation.
        """
        # In a real app, we would fetch from Feast or cache
        # For now, return a random vector
        np.random.seed(hash(user_id) % 2**32)
        return np.random.randn(settings.user_feature_dim).astype(np.float32)

    def get_product_feature_vector(self, product_id: str, feature_store) -> np.ndarray:
        """
        Get product feature vector from feature store.
        Placeholder implementation.
        """
        np.random.seed(hash(product_id) % 2**32)
        return np.random.randn(settings.product_feature_dim).astype(np.float32)