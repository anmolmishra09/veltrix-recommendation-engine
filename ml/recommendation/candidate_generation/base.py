"""
Base class for candidate generators.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class Candidate:
    def __init__(self, item_id: Any, score: float, source: str):
        self.item_id = item_id
        self.score = score
        self.source = source  # Name of the candidate generator

    def __repr__(self):
        return f"Candidate(item_id={self.item_id}, score={self.score:.4f}, source={self.source})"

class CandidateGenerator(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate(self, user_id: Any, context: dict = None, limit: int = 100) -> List[Candidate]:
        """
        Generate candidate items for a user.

        Args:
            user_id: The ID of the user.
            context: Additional context (e.g., current session, time, etc.).
            limit: Maximum number of candidates to generate.

        Returns:
            List of Candidate objects.
        """
        pass

    def _to_candidate_list(self, item_ids: List[Any], scores: List[float]) -> List[Candidate]:
        """
        Helper to convert item IDs and scores to Candidate objects.

        Args:
            item_ids: List of item IDs.
            scores: List of scores corresponding to item IDs.

        Returns:
            List of Candidate objects.
        """
        if len(item_ids) != len(scores):
            raise ValueError("Length of item_ids and scores must be the same")
        return [Candidate(item_id=item_id, score=score, source=self.name) for item_id, score in zip(item_ids, scores)]