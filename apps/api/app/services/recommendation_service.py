"""
Recommendation service that orchestrates candidate generation, ranking, and filtering.
"""
from typing import List, Dict, Any, Optional, Tuple
from ..core.config import settings
from ..core.repositories import product_repository, user_repository
from .candidate_service import CandidateService
from .ranking_service import RankingService
from .event_service import EventService
from ..core.exceptions import UserNotFoundException, ProductNotFoundException
import logging
import time

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.logger = logger
        self.candidate_service = CandidateService()
        self.ranking_service = RankingService()
        self.event_service = EventService()
        # In a real app, we would also initialize a filter service
        self.logger.info("Recommendation service initialized")

    def get_recommendations(
        self,
        user_id: str,
        k: int = 10,
        candidate_source: str = "hybrid",
        context: Optional[Dict[str, Any]] = None,
        store_event: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations for a user.
        """
        start_time = time.time()
        context = context or {}

        self.logger.info(f"Getting recommendations for user {user_id} with k={k}, source={candidate_source}")

        # Validate user exists (optional, could check via user_repo)
        # For now, we'll assume the user exists; if not, candidate generation will return empty

        # Step 1: Generate candidates
        candidates = self.candidate_service.get_candidates_by_source(
            source=candidate_source,
            user_id=user_id,
            limit=settings.candidate_limit  # e.g., 100
        )
        if not candidates:
            self.logger.warning(f"No candidates generated for user {user_id}")
            return []

        self.logger.debug(f"Generated {len(candidates)} candidates")

        # Step 2: Prepare features for ranking
        # In a real implementation, we would fetch user and product features from the feature store
        # For now, we'll use dummy features
        user_feature_vector = self.ranking_service.get_user_feature_vector(user_id, None)
        product_feature_vectors = []
        valid_candidates = []
        for cand in candidates:
            product_id = cand["item_id"]
            # Validate product exists (optional)
            # For now, we'll assume it exists
            product_feature_vector = self.ranking_service.get_product_feature_vector(product_id, None)
            product_feature_vectors.append(product_feature_vector)
            valid_candidates.append(cand)

        if not product_feature_vectors:
            self.logger.warning(f"No valid product features for candidates")
            return []

        # Step 3: Rank candidates
        scores = self.ranking_service.score_candidates(
            user_feature_vector,
            product_feature_vectors
        )
        if not scores:
            self.logger.warning(f"Ranking returned no scores")
            return []

        # Step 4: Combine candidates with scores
        scored_candidates = []
        for cand, score in zip(valid_candidates, scores):
            cand_copy = cand.copy()
            cand_copy["score"] = float(score)
            scored_candidates.append(cand_copy)

        # Step 5: Sort by score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Step 6: Take top-k
        top_k = scored_candidates[:k]

        # Step 7: Add rank
        for i, rec in enumerate(top_k, start=1):
            rec["rank"] = i

        # Step 8: Publish recommendation event if requested
        if store_event:
            event = {
                "user_id": user_id,
                "recommendations": [
                    {"item_id": r["item_id"], "score": r["score"], "rank": r["rank"]}
                    for r in top_k
                ],
                "context": context,
                "timestamp": time.time(),
                "algorithm": f"{candidate_source}_ranking"
            }
            self.event_service.publish_event(
                topic=settings.recommendations_topic,
                event=event,
                key=user_id
            )

        latency_ms = (time.time() - start_time) * 1000
        self.logger.info(f"Returned {len(top_k)} recommendations for user {user_id} in {latency_ms:.2f}ms")

        return top_k

    def get_recommendations_with_details(
        self,
        user_id: str,
        k: int = 10,
        candidate_source: str = "hybrid",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations with additional metadata (for API responses).
        """
        recommendations = self.get_recommendations(
            user_id=user_id,
            k=k,
            candidate_source=candidate_source,
            context=context
        )
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": candidate_source,
            "context": context or {}
        }