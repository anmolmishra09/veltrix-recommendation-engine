"""
Ranker wrapper to use different ranking models.
"""
from .base import BaseRanker
from .xgboost_ranker import XGBoostRanker
from .lightgbm_ranker import LightGBMRanker
from .neural_ranker import NeuralRanker
import logging
from typing import Union, Literal

logger = logging.getLogger(__name__)

RankerType = Literal['xgboost', 'lightgbm', 'neural']

class RankerWrapper(BaseRanker):
    def __init__(self, ranker_type: RankerType = 'xgboost', **ranker_kwargs):
        """
        Initialize the ranker wrapper.

        Args:
            ranker_type: Type of ranker to use ('xgboost', 'lightgbm', 'neural').
            **ranker_kwargs: Keyword arguments to pass to the ranker constructor.
        """
        super().__init__()
        self.ranker_type = ranker_type
        self.ranker_kwargs = ranker_kwargs
        self.ranker = None
        self._initialize_ranker()

    def _initialize_ranker(self):
        """Initialize the ranker instance based on ranker_type."""
        if self.ranker_type == 'xgboost':
            self.ranker = XGBoostRanker(**self.ranker_kwargs)
        elif self.ranker_type == 'lightgbm':
            self.ranker = LightGBMRanker(**self.ranker_kwargs)
        elif self.ranker_type == 'neural':
            # For neural ranker, we need to know the input_dim, which we might not have yet.
            # We'll set it to None and handle it during training.
            self.ranker = NeuralRanker(input_dim=None, **self.ranker_kwargs)
        else:
            raise ValueError(f"Unsupported ranker type: {self.ranker_type}")

    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]):
        """
        Train the ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,).
        """
        # For neural ranker, we need to set the input_dim if not already set
        if self.ranker_type == 'neural' and hasattr(self.ranker, 'input_dim') and self.ranker.input_dim is None:
            if isinstance(X, pd.DataFrame):
                self.ranker.input_dim = X.shape[1]
            else:
                self.ranker.input_dim = X.shape[1]
            # Rebuild the network with the correct input_dim
            self.ranker._initialize_ranker()  # We'll need to add this method to NeuralRanker, but for now we'll assume it's handled

        self.ranker.train(X, y)
        self.is_trained = self.ranker.is_trained
        if hasattr(self.ranker, 'feature_names'):
            self.feature_names = self.ranker.feature_names

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict scores using the ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).

        Returns:
            Predicted scores of shape (n_samples,).
        """
        if not self.is_trained:
            raise Exception("Ranker has not been trained yet")
        return self.ranker.predict(X)

    def save(self, path: str):
        """
        Save the ranker to a file.

        Args:
            path: Path to save the ranker.
        """
        if not self.is_trained:
            raise Exception("Ranker has not been trained yet")
        self.ranker.save(path)

    def load(self, path: str):
        """
        Load the ranker from a file.

        Args:
            path: Path to the saved ranker.
        """
        self.ranker.load(path)
        self.is_trained = self.ranker.is_trained
        if hasattr(self.ranker, 'feature_names'):
            self.feature_names = self.ranker.feature_names

    def get_feature_importance(self) -> Optional[dict]:
        """
        Get feature importance if available.

        Returns:
            Dictionary mapping feature names to importance scores.
        """
        if hasattr(self.ranker, 'get_feature_importance'):
            return self.ranker.get_feature_importance()
        return None