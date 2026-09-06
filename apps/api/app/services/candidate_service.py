"""
Candidate generation service.
"""
from typing import List, Dict, Any, Optional
from ..core.config import settings
from ..core.repositories import product_repository, user_repository
from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
from ml.recommendation.candidate_generation.popularity import PopularityCandidateGenerator
from ml.recommendation.candidate_generation.hybrid import HybridCandidateGenerator
from ml.embeddings.user_embeddings import UserEmbedding
from ml.embeddings.product_embeddings import ProductEmbedding
import logging

logger = logging.getLogger(__name__)

class CandidateService:
    def __init__(self):
        self.logger = logger
        # Initialize embedding model (would be loaded from MLflow or local files)
        # For now, we'll create dummy embeddings; in production, load proper models
        self.user_embedding = UserEmbedding(embedding_dim=settings.embedding_dim)
        self.product_embedding = ProductEmbedding(embedding_dim=settings.embedding_dim)
        # TODO: Load actual embeddings from trained model

        # Initialize candidate generators
        self.popularity_generator = PopularityCandidateGenerator()
        self.embedding_generator = EmbeddingBasedCandidateGenerator(
            self.user_embedding,
            self.product_embedding
        )
        # Hybrid candidate generator combining multiple sources
        self.hybrid_candidate_generator = HybridCandidateGenerator(
            [self.popularity_generator, self.embedding_generator],
            weights=[0.3, 0.7]  # Example weights
        )

    def get_popularity_candidates(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get popularity-based candidates for a user.
        """
        try:
            candidates = self.popularity_generator.generate_candidates(
                user_id=user_id,
                k=limit
            )
            return [{"item_id": str(c.item_id), "score": float(c.score)} for c in candidates]
        except Exception as e:
            self.logger.error(f"Error generating popularity candidates: {e}")
            return []

    def get_embedding_candidates(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get embedding-based candidates for a user.
        """
        try:
            candidates = self.embedding_generator.generate_candidates(
                user_id=user_id,
                k=limit
            )
            return [{"item_id": str(c.item_id), "score": float(c.score)} for c in candidates]
        except Exception as e:
            self.logger.error(f"Error generating embedding candidates: {e}")
            return []

    def get_hybrid_candidates(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get hybrid candidates for a user.
        """
        try:
            candidates = self.hybrid_candidate_generator.generate_candidates(
                user_id=user_id,
                k=limit
            )
            return [{"item_id": str(c.item_id), "score": float(c.score)} for c in candidates]
        except Exception as e:
            self.logger.error(f"Error generating hybrid candidates: {e}")
            return []

    def get_candidates_by_source(self, source: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get candidates from a specific source.
        """
        if source == "popularity":
            return self.get_popularity_candidates(user_id, limit)
        elif source == "embedding":
            return self.get_embedding_candidates(user_id, limit)
        elif source == "hybrid":
            return self.get_hybrid_candidates(user_id, limit)
        else:
            self.logger.warning(f"Unknown candidate source: {source}")
            return []