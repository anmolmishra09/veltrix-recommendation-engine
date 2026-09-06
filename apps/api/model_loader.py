"""
Model loader for loading and caching models from MLflow.
"""
import os
import torch
import mlflow
import mlflow.pytorch
from typing import Optional
from ml.recommendation.embeddings.model import EmbeddingModel
from ml.recommendation.ranking.model import RankingModel

logger = None  # Will be set by the caller

class ModelLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.embedding_model: Optional[EmbeddingModel] = None
        self.ranking_model: Optional[RankingModel] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_models()

    def _load_models(self):
        """
        Load models from MLflow or fallback to local files.
        """
        try:
            # Set MLflow tracking URI from environment variable
            mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(mlflow_tracking_uri)

            # Load the latest version of the embedding model from MLflow
            embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "embedding_model")
            embedding_model_version = os.getenv("EMBEDDING_MODEL_VERSION", "latest")
            embedding_model_uri = f"models:/{embedding_model_name}/{embedding_model_version}"
            self.embedding_model = mlflow.pytorch.load_model(embedding_model_uri)
            self.embedding_model.to(self.device)
            self.embedding_model.eval()
            logger.info(f"Loaded embedding model from {embedding_model_uri}")

            # Load the latest version of the ranking model from MLflow
            ranking_model_name = os.getenv("RANKING_MODEL_NAME", "ranking_model")
            ranking_model_version = os.getenv("RANKING_MODEL_VERSION", "latest")
            ranking_model_uri = f"models:/{ranking_model_name}/{ranking_model_version}"
            self.ranking_model = mlflow.pytorch.load_model(ranking_model_uri)
            self.ranking_model.to(self.device)
            self.ranking_model.eval()
            logger.info(f"Loaded ranking model from {ranking_model_uri}")
        except Exception as e:
            logger.warning(f"Failed to load models from MLflow: {e}. Falling back to local files.")
            self._load_local_models()

    def _load_local_models(self):
        """
        Load models from local files as a fallback.
        """
        # These paths should be configurable
        embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", "./models/embedding_model.pth")
        ranking_model_path = os.getenv("RANKING_MODEL_PATH", "./models/ranking_model.pth")

        # We need to know the model dimensions
        # For now, we'll hardcode - in a real system, we would store this with the model
        num_users = int(os.getenv("NUM_USERS", "1000"))
        num_products = int(os.getenv("NUM_PRODUCTS", "100"))
        embedding_dim = int(os.getenv("EMBEDDING_DIM", "64"))
        user_feature_dim = int(os.getenv("USER_FEATURE_DIM", "4"))
        product_feature_dim = int(os.getenv("PRODUCT_FEATURE_DIM", "3"))
        hidden_dim = int(os.getenv("HIDDEN_DIM", "128"))

        self.embedding_model = EmbeddingModel(num_users, num_products, embedding_dim)
        self.embedding_model.load_state_dict(torch.load(embedding_model_path, map_location=self.device))
        self.embedding_model.to(self.device)
        self.embedding_model.eval()

        self.ranking_model = RankingModel(user_feature_dim, product_feature_dim, hidden_dim)
        self.ranking_model.load_state_dict(torch.load(ranking_model_path, map_location=self.device))
        self.ranking_model.to(self.device)
        self.ranking_model.eval()

        logger.info(f"Loaded embedding model from {embedding_model_path}")
        logger.info(f"Loaded ranking model from {ranking_model_path}")

    def get_embedding_model(self) -> EmbeddingModel:
        return self.embedding_model

    def get_ranking_model(self) -> RankingModel:
        return self.ranking_model