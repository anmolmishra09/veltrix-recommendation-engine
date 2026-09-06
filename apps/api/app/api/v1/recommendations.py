"""
Recommendations endpoint with experiment tracking and monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import logging
import time
import json
from sqlalchemy.orm import Session

# Import our components
from ml.recommendation.hybrid import HybridRecommender
from ml.recommendation.candidate_generation.hybrid import HybridCandidateGenerator
from ml.recommendation.candidate_generation.collaborative import CollaborativeCandidateGenerator
from ml.recommendation.candidate_generation.content import ContentBasedCandidateGenerator
from ml.recommendation.candidate_generation.popularity import PopularityCandidateGenerator
from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
from ml.embeddings.user_embeddings import UserEmbedding
from ml.embeddings.product_embeddings import ProductEmbedding
from ml.ranking.ranker import RankerWrapper
from ml.cold_start.handler import ColdStartHandler
from ..core.database import SessionLocal, get_db
from ..core.redis import get_redis
from ..core.exceptions import UserNotFoundException, ProductNotFoundException
from ..core.config import settings
from ..core.services import experiment_service
from ..core.repositories import recommendation_repository
from ..core import models
from ..core.monitoring import monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response
class RecommendationRequest(BaseModel):
    user_id: Any = Field(..., description="The ID of the user")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (e.g., time, device, location)")
    candidate_limit: Optional[int] = Field(100, description="Maximum number of candidates to generate from each source")
    top_k: Optional[int] = Field(10, description="Number of recommendations to return")
    ranking_model: Optional[str] = Field("xgboost", description="Ranking model to use (xgboost, lightgbm, neural)")

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    user_id: Any
    context: Optional[Dict[str, Any]]
    ranking_model_used: str
    latency_ms: float
    experiment_id: Optional[str] = None
    experiment_variant: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# We'll create a mock initializer for the components
# In a real application, these would be initialized once at startup and stored in the app state
def get_recommender_components():
    """
    Initialize and return the recommender components.
    This is a placeholder. In a real app, you would load pretrained models, etc.
    """
    logger.info("Initializing recommender components (mock)")

    # Initialize embeddings (mock)
    user_embedding = UserEmbedding(embedding_dim=64)
    product_embedding = ProductEmbedding(embedding_dim=64)
    # In a real app, you would load the embeddings from files or a database
    # For now, we'll leave them empty (they will return zero vectors)

    # Initialize candidate generators
    collaborative_generator = CollaborativeCandidateGenerator()
    content_generator = ContentBasedCandidateGenerator()
    popularity_generator = PopularityCandidateGenerator()
    embedding_generator = EmbeddingBasedCandidateGenerator(user_embedding, product_embedding)

    # Initialize hybrid candidate generator
    candidate_generators = [
        collaborative_generator,
        content_generator,
        popularity_generator,
        embedding_generator
    ]
    # Equal weights for the hybrid candidate generator
    hybrid_candidate_generator = HybridCandidateGenerator(candidate_generators, weights=[0.25, 0.25, 0.25, 0.25])

    # Initialize ranker
    ranker = RankerWrapper(ranker_type="xgboost")
    # In a real app, you would load a pretrained ranker

    # Initialize hybrid recommender (for combining scores from different sources)
    hybrid_recommender = HybridRecommender(
        collaborative_weight=0.35,
        content_weight=0.25,
        popularity_weight=0.15,
        embedding_weight=0.25
    )

    # Initialize cold start handler
    cold_start_handler = ColdStartHandler(
        hybrid_recommender=hybrid_recommender,
        popularity_candidates=[("product_1", 10.0), ("product_2", 8.0), ("product_3", 6.0)],  # Mock data
        trending_candidates=[("product_4", 9.0), ("product_5", 7.0)],  # Mock data
        category_popularity={}  # Mock data
    )

    return {
        "user_embedding": user_embedding,
        "product_embedding": product_embedding,
        "collaborative_generator": collaborative_generator,
        "content_generator": content_generator,
        "popularity_generator": popularity_generator,
        "embedding_generator": embedding_generator,
        "hybrid_candidate_generator": hybrid_candidate_generator,
        "ranker": ranker,
        "hybrid_recommender": hybrid_recommender,
        "cold_start_handler": cold_start_handler
    }

# We'll use a simple caching mechanism for the components
_components_cache = None

def get_components():
    global _components_cache
    if _components_cache is None:
        _components_cache = get_recommender_components()
    return _components_cache

@router.post("/", response_model=RecommendationResponse)
@monitoring_service.time_api_request(method="POST", endpoint="/recommendations/")
def get_recommendations(
    request: RecommendationRequest,
    components: dict = Depends(get_components),
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis),
    req: Request = None
):
    """
    Get recommendations for a user with experiment tracking.
    """
    start_time = time.time()

    user_id = request.user_id
    context = request.context or {}
    candidate_limit = request.candidate_limit
    top_k = request.top_k
    ranking_model_type = request.ranking_model

    # Calculate request size (approximate)
    request_size = len(json.dumps(request.dict()).encode('utf-8'))

    logger.info(f"Getting recommendations for user {user_id} with context {context}")

    # Initialize services
    experiment_svc = experiment_service.ExperimentService(db)
    recommendation_repo = recommendation_repository.RecommendationRepository(db)

    # Check for experiment assignments
    experiment_id = None
    experiment_variant = None
    model_version_to_use = ranking_model_type  # Default to requested model

    # Check if there's an active experiment for ranking models
    try:
        # Try to get the ranking_v2 experiment (example from the task description)
        experiment_exp = experiment_svc.get_experiment("ranking_v2")
        if experiment_exp and experiment_exp.status == "active":
            # Get user's variant assignment
            assignment_result = experiment_svc.get_user_variant("ranking_v2", int(user_id) if isinstance(user_id, str) and user_id.isdigit() else hash(user_id))
            experiment_id = assignment_result["experiment_id"]
            experiment_variant = assignment_result["variant"]
            model_version_to_use = assignment_result.get("model_version") or ranking_model_type

            # Track experiment exposure
            experiment_svc.track_experiment_exposure(
                experiment_id=experiment_id,
                user_id=int(user_id) if isinstance(user_id, str) and user_id.isdigit() else hash(user_id),
                variant=experiment_variant,
                context=context
            )

            logger.info(f"User {user_id} assigned to variant '{experiment_variant}' of experiment '{experiment_id}' using model '{model_version_to_use}'")
    except Exception as e:
        logger.warning(f"Could not check experiment assignments: {e}")
        # Continue with default model if experiment checking fails

    # Check if we should use cold start for new user
    # In a real app, we would check if the user has any interactions
    # For now, we'll assume all users are existing users

    # Generate candidates from each source
    logger.info("Generating candidates from collaborative filtering")
    collaborative_candidates = components["collaborative_generator"].generate(
        user_id=user_id,
        context=context,
        limit=candidate_limit
    )

    logger.info("Generating candidates from content-based")
    content_candidates = components["content_generator"].generate(
        user_id=user_id,
        context=context,
        limit=candidate_limit
    )

    logger.info("Generating candidates from popularity")
    popularity_candidates = components["popularity_generator"].generate(
        user_id=user_id,
        context=context,
        limit=candidate_limit
    )

    logger.info("Generating candidates from embedding")
    embedding_candidates = components["embedding_generator"].generate(
        user_id=user_id,
        context=context,
        limit=candidate_limit
    )

    # Convert candidates to scores dictionaries
    def candidates_to_scores(candidates):
        return {candidate.item_id: candidate.score for candidate in candidates}

    collaborative_scores = candidates_to_scores(collaborative_candidates)
    content_scores = candidates_to_scores(content_candidates)
    popularity_scores = candidates_to_scores(popularity_candidates)
    embedding_scores = candidates_to_scores(embedding_candidates)

    # Combine scores using the hybrid recommender
    logger.info("Combining scores from different sources")
    combined_scores = components["hybrid_recommender"].combine_scores(
        collaborative_scores=collaborative_scores,
        content_scores=content_scores,
        popularity_scores=popularity_scores,
        embedding_scores=embedding_scores
    )

    # If we have no combined scores, fall back to cold start
    if not combined_scores:
        logger.warning("No combined scores generated. Using cold start for new user.")
        cold_start_recommendations = components["cold_start_handler"].handle_new_user(
            context=context,
            top_k=candidate_limit
        )
        combined_scores = {item_id: score for item_id, score in cold_start_recommendations}

    # Prepare features for ranking
    # In a real app, we would fetch user and product features from the feature store
    # For now, we'll skip ranking and just use the combined scores
    # TODO: Implement feature fetching and ranking

    # Get top-K recommendations
    sorted_recommendations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    top_recommendations = sorted_recommendations[:top_k]

    # Format the response
    recommendations_list = []
    for rank, (item_id, score) in enumerate(top_recommendations, start=1):
        recommendations_list.append({
            "item_id": item_id,
            "score": float(score),
            "rank": rank,
            "source": "hybrid"  # We could track the source per item, but for simplicity we'll use hybrid
        })

    # Store recommendations in database for tracking
    try:
        if recommendations_list:
            # Create a recommendation record
            rec_record = models.Recommendation(
                user_id=int(user_id) if isinstance(user_id, str) and user_id.isdigit() else hash(user_id),
                context_=context,
                model_version=model_version_to_use,
                experiment_id=experiment_id,
                num_candidates=len(collaborative_candidates) + len(content_candidates) + len(popularity_candidates) + len(embedding_candidates),
                num_returned=len(recommendations_list)
            )
            stored_recommendation = recommendation_repo.create_recommendation(rec_record)
            logger.info(f"Stored recommendation record ID {stored_recommendation.id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to store recommendation record: {e}")
        # Don't fail the request if we can't store the record

    latency_ms = (time.time() - start_time) * 1000

    # Calculate response size (approximate)
    response_data = {
        "recommendations": recommendations_list,
        "user_id": user_id,
        "context": context,
        "ranking_model_used": model_version_to_use,
        "latency_ms": latency_ms,
        "experiment_id": experiment_id,
        "experiment_variant": experiment_variant,
        "metadata": {
            "candidate_counts": {
                "collaborative": len(collaborative_candidates),
                "content": len(content_candidates),
                "popularity": len(popularity_candidates),
                "embedding": len(embedding_candidates)
            }
        }
    }
    response_size = len(json.dumps(response_data).encode('utf-8'))

    response = RecommendationResponse(
        recommendations=recommendations_list,
        user_id=user_id,
        context=context,
        ranking_model_used=model_version_to_use,
        latency_ms=latency_ms,
        experiment_id=experiment_id,
        experiment_variant=experiment_variant,
        metadata={
            "candidate_counts": {
                "collaborative": len(collaborative_candidates),
                "content": len(content_candidates),
                "popularity": len(popularity_candidates),
                "embedding": len(embedding_candidates)
            }
        }
    )

    # Record API metrics
    monitoring_service.record_api_request(
        method="POST",
        endpoint="/recommendations/",
        status_code=200,
        request_size=request_size,
        response_size=response_size
    )

    logger.info(f"Returned {len(recommendations_list)} recommendations for user {user_id} in {latency_ms:.2f}ms")
    return response