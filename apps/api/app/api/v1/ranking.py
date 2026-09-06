"""
Ranking endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional, Dict
import logging
import time

from ml.ranking.ranker import RankerWrapper
from ..core.database import SessionLocal
from ..core.redis import get_redis
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class RankingRequest(BaseModel):
    user_id: Any = Field(..., description="The ID of the user")
    item_ids: List[Any] = Field(..., description="List of item IDs to rank")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    model_type: Optional[str] = Field("xgboost", description="Ranking model to use (xgboost, lightgbm, neural)")

class RankingResponse(BaseModel):
    rankings: List[Dict[str, Any]]
    user_id: Any
    model_used: str
    latency_ms: float

# We'll reuse the component initializer from the recommendations endpoint
def get_recommender_components():
    from ml.recommendation.hybrid import HybridRecommender
    from ml.recommendation.candidate_generation.hybrid import HybridCandidateGenerator
    from ml.recommendation.candidate_generation.collaborative import CollaborativeCandidateGenerator
    from ml.recommendation.candidate_generation.content import ContentBasedCandidateGenerator
    from ml.recommendation.candidate_generation.popularity import PopularityCandidateGenerator
    from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
    from ml.embeddings.user_embeddings import UserEmbedding
    from ml.embeddings.product_embeddings import ProductEmbedding
    from ml.ranking.ranker import RankerWrapper
    logger.info("Initializing recommender components for ranking (mock)")

    # Initialize embeddings (mock)
    user_embedding = UserEmbedding(embedding_dim=64)
    product_embedding = ProductEmbedding(embedding_dim=64)

    # Initialize ranker
    ranker = RankerWrapper(ranker_type="xgboost")

    return {
        "user_embedding": user_embedding,
        "product_embedding": product_embedding,
        "ranker": ranker
    }

_components_cache = None

def get_components():
    global _components_cache
    if _components_cache is None:
        _components_cache = get_recommender_components()
    return _components_cache

@router.post("/", response_model=RankingResponse)
def rank_items(
    request: RankingRequest,
    components: dict = Depends(get_components),
    db: Session = Depends(SessionLocal),
    redis_client = Depends(get_redis)
):
    """
    Rank a list of items for a user.
    """
    start_time = time.time()

    user_id = request.user_id
    item_ids = request.item_ids
    context = request.context or {}
    model_type = request.model_type

    logger.info(f"Ranking {len(item_ids)} items for user {user_id} with model {model_type}")

    # TODO: Validate user and items exist
    # TODO: Fetch features for user and items from feature store
    # TODO: Rank the items using the ranker

    # For now, we'll return random scores
    import random
    rankings = []
    for rank, item_id in enumerate(item_ids, start=1):
        score = random.random()
        rankings.append({
            "item_id": item_id,
            "score": score,
            "rank": rank
        })

    # Sort by score descending
    rankings.sort(key=lambda x: x["score"], reverse=True)
    # Re-rank
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank

    latency_ms = (time.time() - start_time) * 1000

    response = RankingResponse(
        rankings=rankings,
        user_id=user_id,
        model_used=model_type,
        latency_ms=latency_ms
    )

    logger.info(f"Ranked {len(item_ids)} items for user {user_id} in {latency_ms:.2f}ms")
    return response