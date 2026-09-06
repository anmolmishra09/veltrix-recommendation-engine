"""
XGBoost ranker.
"""
import xgboost as xgb
from .base import BaseRanker
import logging
import numpy as np
import pandas as pd
import os
import json
from typing import Union, Optional

logger = logging.getLogger(__name__)

class XGBoostRanker(BaseRanker):
    def __init__(self, **xgb_params):
        """
        Initialize the XGBoost ranker.

        Args:
            **xgb_params: Parameters for XGBoost ranker (e.g., objective='rank:pairwise', learning_rate=0.1, etc.)
        """
        super().__init__()
        self.xgb_params = xgb_params
        self.model = None

    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]):
        """
        Train the XGBoost ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,).
        """
        # Convert to DMatrix
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

        # Create DMatrix
        dtrain = xgb.DMatrix(X_matrix, label=y_array)

        # Set default parameters if not provided
        params = {
            'objective': 'rank:pairwise',
            'eval_metric': 'ndcg',
            'learning_rate': 0.1,
            'max_depth': 6,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
        }
        params.update(self.xgb_params)

        # Train the model
        self.model = xgb.train(params, dtrain, num_boost_round=100)
        self.is_trained = True
        logger.info("XGBoost ranker trained successfully")

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict scores using the XGBoost ranker.

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

        dtest = xgb.DMatrix(X_matrix)
        predictions = self.model.predict(dtest)
        return predictions

    def save(self, path: str):
        """
        Save the XGBoost ranker to a file.

        Args:
            path: Path to save the ranker (without extension).
        """
        if not self.is_trained:
            raise Exception("Model has not been trained yet")

        # Save the model
        model_path = f"{path}.model"
        self.model.save_model(model_path)

        # Save feature names and parameters
        metadata = {
            'feature_names': self.feature_names,
            'xgb_params': self.xgb_params
        }
        metadata_path = f"{path}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        logger.info(f"XGBoost ranker saved to {model_path} and {metadata_path}")

    def load(self, path: str):
        """
        Load the XGBoost ranker from a file.

        Args:
            path: Path to the saved ranker (without extension).
        """
        # Load the model
        model_path = f"{path}.model"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        self.model = xgb.Booster()
        self.model.load_model(model_path)

        # Load feature names and parameters
        metadata_path = f"{path}.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.feature_names = metadata.get('feature_names')
            self.xgb_params = metadata.get('xgb_params', {})
        else:
            logger.warning(f"Metadata file not found: {metadata_path}")

        self.is_trained = True
        logger.info(f"XGBoost ranker loaded from {model_path}")

    def get_feature_importance(self) -> Optional[dict]:
        """
        Get feature importance from the XGBoost model.

        Returns:
            Dictionary mapping feature names to importance scores.
        """
        if not self.is_trained or self.feature_names is None:
            return None

        importance = self.model.get_score(importance_type='gain')
        # Map feature names (XGBoost uses f0, f1, etc. by default)
        # We need to map from f0, f1 to actual feature names
        if self.feature_names is not None:
            mapped_importance = {}
            for f_id, score in importance.items():
                # f_id is like 'f0', 'f1', etc.
                idx = int(f_id[1:])
                if idx < len(self.feature_names):
                    mapped_importance[self.feature_names[idx]] = score
                else:
                    mapped_importance[f_id] = score
            return mapped_importance
        else:
            return importance