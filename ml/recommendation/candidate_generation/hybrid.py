"""
Hybrid candidate generator that combines multiple candidate generators.
"""
from .base import CandidateGenerator, Candidate
import numpy as np
from typing import List, Tuple, Any, Optional, Union, Dict
import logging

logger = logging.getLogger(__name__)

class HybridCandidateGenerator(CandidateGenerator):
    def __init__(self, generators: List[CandidateGenerator], weights: List[float] = None):
        """
        Initialize the hybrid candidate generator.

        Args:
            generators: List of candidate generator instances.
            weights: List of weights for each generator. If None, equal weights are used.
                    The weights will be normalized to sum to 1.
        """
        super().__init__("hybrid")
        self.generators = generators
        if weights is None:
            weights = [1.0] * len(generators)
        if len(weights) != len(generators):
            raise ValueError("Length of weights must match length of generators")
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            self.weights = [0.0] * len(generators)
        else:
            self.weights = [w / total_weight for w in weights]
        logger.info(f"Initialized hybrid candidate generator with {len(generators)} generators and weights {self.weights}")

    def generate(self, user_id: Any, context: dict = None, limit: int = 100) -> List[Candidate]:
        """
        Generate candidates by combining scores from multiple generators.

        Args:
            user_id: The ID of the user.
            context: Additional context.
            limit: Maximum number of candidates to generate.

        Returns:
            List of Candidate objects.
        """
        # We'll collect candidates from each generator and combine their scores
        # We'll ask each generator for more candidates than the limit to have enough to combine
        # We'll use a factor of 3 to get more candidates
        candidate_limit = limit * 3

        # Dictionary to store combined scores for each item
        combined_scores = {}

        for i, generator in enumerate(self.generators):
            weight = self.weights[i]
            if weight == 0:
                continue

            try:
                # Generate candidates from this generator
                candidates = generator.generate(user_id=user_id, context=context, limit=candidate_limit)
                # Add weighted scores to combined_scores
                for candidate in candidates:
                    item_id = candidate.item_id
                    if item_id not in combined_scores:
                        combined_scores[item_id] = 0.0
                    combined_scores[item_id] += weight * candidate.score
            except Exception as e:
                logger.warning(f"Generator {generator.name} failed to generate candidates: {e}")
                continue

        # Sort items by combined score descending
        sorted_items = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        # Take top 'limit'
        top_items = sorted_items[:limit]

        item_ids = [item[0] for item in top_items]
        scores = [item[1] for item in top_items]

        return [Candidate(item_id=item_id, score=score, source=self.name) for item_id, score in zip(item_ids, scores)]