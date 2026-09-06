"""
Tests for the recommendation system.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

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

def test_hybrid_recommender_initialization():
    """
    Test that the hybrid recommender initializes correctly with default weights.
    """
    recommender = HybridRecommender()

    # Check that weights are normalized to sum to 1
    assert abs(recommender.collaborative_weight + recommender.content_weight +
               recommender.popularity_weight + recommender.embedding_weight - 1.0) < 1e-10

    # Check that all weights are non-negative
    assert recommender.collaborative_weight >= 0
    assert recommender.content_weight >= 0
    assert recommender.popularity_weight >= 0
    assert recommender.embedding_weight >= 0

def test_hybrid_recommender_custom_weights():
    """
    Test that the hybrid recommender accepts custom weights.
    """
    recommender = HybridRecommender(
        collaborative_weight=0.5,
        content_weight=0.3,
        popularity_weight=0.1,
        embedding_weight=0.1
    )

    # Check that weights are set correctly (should be normalized)
    total_weight = 0.5 + 0.3 + 0.1 + 0.1  # 1.0
    assert abs(recommender.collaborative_weight - 0.5/total_weight) < 1e-10
    assert abs(recommender.content_weight - 0.3/total_weight) < 1e-10
    assert abs(recommender.popularity_weight - 0.1/total_weight) < 1e-10
    assert abs(recommender.embedding_weight - 0.1/total_weight) < 1e-10

def test_candidate_generator_base():
    """
    Test the base candidate generator and candidate class.
    """
    from ml.recommendation.candidate_generation.base import Candidate

    # Test Candidate creation
    candidate = Candidate(item_id="item_1", score=0.8, source="test")
    assert candidate.item_id == "item_1"
    assert candidate.score == 0.8
    assert candidate.source == "test"

    # Test string representation
    assert "item_id=item_1" in str(candidate)
    assert "score=0.8" in str(candidate)
    assert "source=test" in str(candidate)

def test_cold_start_handler():
    """
    Test the cold start handler.
    """
    # Create a mock hybrid recommender
    hybrid_recommender = Mock()
    hybrid_recommender.recommend.return_value = [("item_1", 0.9), ("item_2", 0.8)]

    # Create cold start handler
    handler = ColdStartHandler(
        hybrid_recommender=hybrid_recommender,
        popularity_candidates=[("item_3", 1.0), ("item_4", 0.8)],
        trending_candidates=[("item_5", 0.9)],
        category_popularity={"category_1": [("item_6", 0.7), ("item_7", 0.6)]}
    )

    # Test new user handling
    recommendations = handler.handle_new_user(context={"category": "category_1"}, top_k=5)

    # Should return a list of tuples
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 5
    assert all(isinstance(rec, tuple) and len(rec) == 2 for rec in recommendations)

    # Test new product handling (fallback)
    recommendations = handler.handle_new_product(user_id="user_1", top_k=3)
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 3

def test_embedding_based_candidate_generator():
    """
    Test the embedding-based candidate generator.
    """
    # Create mock embeddings
    user_embedding = Mock(spec=UserEmbedding)
    user_embedding.get_embedding.return_value = np.array([0.1, 0.2, 0.3])

    product_embedding = Mock(spec=ProductEmbedding)
    product_embedding.id_to_index = {"product_1": 0, "product_2": 1}
    product_embedding.get_embeddings.return_value = np.array([
        [0.1, 0.2, 0.3],  # product_1
        [0.2, 0.1, 0.4]   # product_2
    ])

    # Create generator
    generator = EmbeddingBasedCandidateGenerator(user_embedding, product_embedding)

    # Generate candidates
    candidates = generator.generate(user_id="user_1", limit=2)

    # Should return candidates
    assert isinstance(candidates, list)
    assert len(candidates) <= 2
    assert all(hasattr(c, 'item_id') and hasattr(c, 'score') and hasattr(c, 'source') for c in candidates)
    assert all(c.source == "embedding" for c in candidates)

if __name__ == "__main__":
    # Run tests
    test_hybrid_recommender_initialization()
    test_hybrid_recommender_custom_weights()
    test_candidate_generator_base()
    test_cold_start_handler()
    test_embedding_based_candidate_generator()
    print("All tests passed!")