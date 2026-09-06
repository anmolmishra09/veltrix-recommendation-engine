"""
Base class for rankers.
"""
from abc import ABC, abstractmethod
import logging
from typing import List, Tuple, Any, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class BaseRanker(ABC):
    def __init__(self):
        self.is_trained = False
        self.feature_names = None

    @abstractmethod
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]):
        """
        Train the ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,). For ranking, this is usually the relevance score.
        """
        pass

    @abstractmethod
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict scores for the given features.

        Args:
            X: Feature matrix of shape (n_samples, n_features).

        Returns:
            Predicted scores of shape (n_samples,).
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """
        Save the ranker to a file.

        Args:
            path: Path to save the ranker.
        """
        pass

    @abstractmethod
    def load(self, path: str):
        """
        Load the ranker from a file.

        Args:
            path: Path to the saved ranker.
        """
        pass

    def get_feature_importance(self) -> Optional[dict]:
        """
        Get feature importance if available.

        Returns:
            Dictionary mapping feature names to importance scores, or None if not available.
        """
        return None

    def set_feature_names(self, feature_names: List[str]):
        """
        Set the feature names for interpretability.

        Args:
            feature_names: List of feature names.
        """
        self.feature_names = feature_names