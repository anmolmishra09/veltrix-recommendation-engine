"""
Embedding-based candidate generator.
"""
import numpy as np
from .base import CandidateGenerator, Candidate
from ...embeddings.user_embeddings import UserEmbedding
from ...embeddings.product_embeddings import ProductEmbedding
from ...embeddings.similarity import cosine_similarity_batch
import logging
from typing import List, Tuple, Any, Optional, Union

logger = logging.getLogger(__name__)

class EmbeddingBasedCandidateGenerator(CandidateGenerator):
    def __init__(self, user_embedding: UserEmbedding, product_embedding: ProductEmbedding):
        """
        Initialize the embedding-based candidate generator.

        Args:
            user_embedding: UserEmbedding instance.
            product_embedding: ProductEmbedding instance.
        """
        super().__init__("embedding")
        self.user_embedding = user_embedding
        self.product_embedding = product_embedding

        # Precompute product embeddings for all products to speed up similarity search
        self._precompute_product_embeddings()

    def _precompute_product_embeddings(self):
        """Precompute product embeddings for all products."""
        # Get all product IDs from the product embedding
        product_ids = list(self.product_embedding.id_to_index.keys())
        self.product_ids = np.array(product_ids, dtype=object)
        self.product_embeddings = self.product_embedding.get_embeddings(product_ids)
        logger.info(f"Precomputed embeddings for {len(self.product_ids)} products")

    def generate(self, user_id: Any, context: dict = None, limit: int = 100) -> List[Candidate]:
        """
        Generate candidates based on embedding similarity between user and products.

        Args:
            user_id: The ID of the user.
            context: Additional context (not used).
            limit: Maximum number of candidates to generate.

        Returns:
            List of Candidate objects sorted by similarity descending.
        """
        try:
            # Get user embedding
            user_emb = self.user_embedding.get_embedding(user_id)
        except Exception as e:
            logger.warning(f"Could not get embedding for user {user_id}: {e}. Returning empty candidates.")
            return []

        # Compute similarity with all products
        similarities = cosine_similarity_batch(user_emb, self.product_embeddings)

        # Get top-k product indices
        top_k_indices = np.argsort(similarities)[::-1][:limit]
        top_k_product_ids = self.product_ids[top_k_indices]
        top_k_scores = similarities[top_k_indices]

        # Convert to list of Candidates
        candidates = []
        for product_id, score in zip(top_k_product_ids, top_k_scores):
            candidates.append(Candidate(item_id=product_id, score=score, source=self.name))

        return candidates