"""
Hybrid recommender that combines multiple recommendation sources.
"""
from ml.recommendation.candidate_generation.base import Candidate
import logging
from typing import List, Tuple, Any, Optional, Union, Dict
import numpy as np

logger = logging.getLogger(__name__)

class HybridRecommender:
    def __init__(self,
                 collaborative_weight: float = 0.35,
                 content_weight: float = 0.25,
                 popularity_weight: float = 0.15,
                 embedding_weight: float = 0.25):
        """
        Initialize the hybrid recommender.

        Args:
            collaborative_weight: Weight for collaborative filtering scores.
            content_weight: Weight for content-based scores.
            popularity_weight: Weight for popularity scores.
            embedding_weight: Weight for embedding similarity scores.
        """
        self.collaborative_weight = collaborative_weight
        self.content_weight = content_weight
        self.popularity_weight = popularity_weight
        self.embedding_weight = embedding_weight

        # Normalize weights to sum to 1
        total_weight = collaborative_weight + content_weight + popularity_weight + embedding_weight
        if total_weight == 0:
            raise ValueError("At least one weight must be non-zero")
        self.collaborative_weight /= total_weight
        self.content_weight /= total_weight
        self.popularity_weight /= total_weight
        self.embedding_weight /= total_weight

        logger.info(f"Initialized hybrid recommender with weights: "
                    f"collaborative={self.collaborative_weight:.2f}, "
                    f"content={self.content_weight:.2f}, "
                    f"popularity={self.popularity_weight:.2f}, "
                    f"embedding={self.embedding_weight:.2f}")

    def combine_scores(self,
                       collaborative_scores: Dict[Any, float] = None,
                       content_scores: Dict[Any, float] = None,
                       popularity_scores: Dict[Any, float] = None,
                       embedding_scores: Dict[Any, float] = None) -> Dict[Any, float]:
        """
        Combine scores from different sources.

        Args:
            collaborative_scores: Dictionary mapping item IDs to collaborative filtering scores.
            content_scores: Dictionary mapping item IDs to content-based scores.
            popularity_scores: Dictionary mapping item IDs to popularity scores.
            embedding_scores: Dictionary mapping item IDs to embedding similarity scores.

        Returns:
            Dictionary mapping item IDs to combined scores.
        """
        # Initialize combined scores dictionary
        combined_scores = {}

        # List of score dictionaries and their weights
        score_sources = [
            (collaborative_scores, self.collaborative_weight),
            (content_scores, self.content_weight),
            (popularity_scores, self.popularity_weight),
            (embedding_scores, self.embedding_weight)
        ]

        # Iterate over each score source
        for scores, weight in score_sources:
            if scores is None:
                continue
            for item_id, score in scores.items():
                if item_id not in combined_scores:
                    combined_scores[item_id] = 0.0
                combined_scores[item_id] += weight * score

        return combined_scores

    def recommend(self,
                  user_id: Any,
                  collaborative_scores: Dict[Any, float] = None,
                  content_scores: Dict[Any, float] = None,
                  popularity_scores: Dict[Any, float] = None,
                  embedding_scores: Dict[Any, float] = None,
                  top_k: int = 10) -> List[Tuple[Any, float]]:
        """
        Generate hybrid recommendations.

        Args:
            user_id: The ID of the user.
            collaborative_scores: Dictionary mapping item IDs to collaborative filtering scores.
            content_scores: Dictionary mapping item IDs to content-based scores.
            popularity_scores: Dictionary mapping item IDs to popularity scores.
            embedding_scores: Dictionary mapping item IDs to embedding similarity scores.
            top_k: Number of recommendations to return.

        Returns:
            List of tuples (item_id, combined_score) sorted by score descending.
        """
        # Combine scores
        combined_scores = self.combine_scores(
            collaborative_scores=collaborative_scores,
            content_scores=content_scores,
            popularity_scores=popularity_scores,
            embedding_scores=embedding_scores
        )

        # Sort by score descending
        sorted_recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top-k
        return sorted_recommendations[:top_k]