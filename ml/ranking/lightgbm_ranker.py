"""
LightGBM ranker.
"""
import lightgbm as lgb
from .base import BaseRanker
import logging
import numpy as np
import pandas as pd
import os
import json
from typing import Union, Optional

logger = logging.getLogger(__name__)

class LightGBMRanker(BaseRanker):
    def __init__(self, **lgb_params):
        """
        Initialize the LightGBM ranker.

        Args:
            **lgb_params: Parameters for LightGBM ranker (e.g., objective='lambdarank', learning_rate=0.1, etc.)
        """
        super().__init__()
        self.lgb_params = lgb_params
        self.model = None

    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]):
        """
        Train the LightGBM ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,).
        """
        # Convert to LightGBM Dataset
        if isinstance(X, pd.DataFrame):
            if self.feature_names is None:
                self.feature_names = list(X.columns)
            X_matrix = X.values
        else:
            X_matrix = X

        if isinstance(y, pd.Series):
            y_array = y.values
        else:
            y_array = y

        # Create Dataset
        train_data = lgb.Dataset(X_matrix, label=y_array)

        # Set default parameters if not provided
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'learning_rate': 0.1,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
        }
        params.update(self.lgb_params)

        # Train the model
        self.model = lgb.train(params, train_data, num_boost_round=100)
        self.is_trained = True
        logger.info("LightGBM ranker trained successfully")

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict scores using the LightGBM ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).

        Returns:
            Predicted scores of shape (n_samples,).
        """
        if not self.is_trained:
            raise Exception("Model has not been trained yet")

        if isinstance(X, pd.DataFrame):
            X_matrix = X.values
        else:
            X_matrix = X

        predictions = self.model.predict(X_matrix, num_iteration=self.model.best_iteration)
        return predictions

    def save(self, path: str):
        """
        Save the LightGBM ranker to a file.

        Args:
            path: Path to save the ranker (without extension).
        """
        if not self.is_trained:
            raise Exception("Model has not been trained yet")

        # Save the model
        model_path = f"{path}.txt"
        self.model.save_model(model_path)

        # Save feature names and parameters
        metadata = {
            'feature_names': self.feature_names,
            'lgb_params': self.lgb_params
        }
        metadata_path = f"{path}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        logger.info(f"LightGBM ranker saved to {model_path} and {metadata_path}")

    def load(self, path: str):
        """
        Load the LightGBM ranker from a file.

        Args:
            path: Path to the saved ranker (without extension).
        """
        # Load the model
        model_path = f"{path}.txt"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        self.model = lgb.Booster(model_file=model_path)

        # Load feature names and parameters
        metadata_path = f"{path}.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.feature_names = metadata.get('feature_names')
            self.lgb_params = metadata.get('lgb_params', {})
        else:
            logger.warning(f"Metadata file not found: {metadata_path}")

        self.is_trained = True
        logger.info(f"LightGBM ranker loaded from {model_path}")

    def get_feature_importance(self) -> Optional[dict]:
        """
        Get feature importance from the LightGBM model.

        Returns:
            Dictionary mapping feature names to importance scores.
        """
        if not self.is_trained or self.feature_names is None:
            return None

        importance = self.model.feature_importance(importance_type='gain')
        # Create dictionary mapping feature names to importance
        if self.feature_names is not None and len(self.feature_names) == len(importance):
            return dict(zip(self.feature_names, importance))
        else:
            logger.warning("Feature names length does not match importance length")
            return None