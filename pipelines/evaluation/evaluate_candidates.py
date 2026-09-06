"""
Evaluation script for candidate generation.
"""
import pandas as pd
import numpy as np
import os
import logging
import json
from typing import Dict, List, Tuple, Any
from ml.recommendation.candidate_generation.hybrid import HybridCandidateGenerator
from ml.recommendation.candidate_generation.collaborative import CollaborativeCandidateGenerator
from ml.recommendation.candidate_generation.content import ContentBasedCandidateGenerator
from ml.recommendation.candidate_generation.popularity import PopularityCandidateGenerator
from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
from ml.embeddings.user_embeddings import UserEmbedding
from ml.embeddings.product_embeddings import ProductEmbedding

logger = logging.getLogger(__name__)

def load_test_data():
    """
    Load test data for evaluation.
    In a real implementation, this would load a held-out test set.
    """
    # For demonstration, we'll create some dummy test data
    logger.info("Loading test data for candidate generation evaluation")

    # Create dummy test interactions
    test_interactions = pd.Data({
        'user_id': [f'user_{i}' for i in range(1, 21)],
        'product_id': [f'product_{i}' for i in range(1, 11)],
        'event_type': ['purchase'] * 20,  # All purchases for simplicity
        'timestamp': pd.date_range('2026-09-01', periods=20, freq='H')
    })

    return test_interactions

def calculate_hit_at_k(recommendations: List[Any], actual: Any, k: int = 10) -> float:
    """
    Calculate Hit@K metric.
    """
    if actual in recommendations[:k]:
        return 1.0
    return 0.0

def calculate_mrr(recommendations: List[Any], actual: Any) -> float:
    """
    Calculate Mean Reciprocal Rank.
    """
    try:
        rank = recommendations.index(actual) + 1
        return 1.0 / rank
    except ValueError:
        return 0.0

def evaluate_candidate_generator(generator, test_data: pd.DataFrame, k_values: List[int] = [1, 5, 10]) -> Dict[str, float]:
    """
    Evaluate a candidate generator.

    Args:
        generator: Candidate generator instance.
        test_data: DataFrame with columns ['user_id', 'product_id'] representing actual interactions.
        k_values: List of K values to calculate Hit@K for.

    Returns:
        Dictionary of evaluation metrics.
    """
    logger.info(f"Evaluating candidate generator: {generator.name}")

    hit_at_k_scores = {f'hit_at_{k}': [] for k in k_values}
    mrr_scores = []

    # For each user in test data
    for user_id in test_data['user_id'].unique():
        user_actual_items = test_data[test_data['user_id'] == user_id]['product_id'].tolist()

        # Generate candidates for this user
        try:
            candidates = generator.generate(user_id=user_id, limit=max(k_values))
            recommended_items = [candidate.item_id for candidate in candidates]
        except Exception as e:
            logger.warning(f"Error generating candidates for user {user_id}: {e}")
            continue

        # Calculate metrics for each actual item
        for actual_item in user_actual_items:
            hit_at_k_scores_list = []
            for k in k_values:
                hit_at_k_scores_list.append(calculate_hit_at_k(recommended_items, actual_item, k))
            # Average across k values for this item
            for i, k in enumerate(k_values):
                hit_at_k_scores[f'hit_at_{k}'].append(hit_at_k_scores_list[i])

            mrr_scores.append(calculate_mrr(recommended_items, actual_item))

    # Calculate average metrics
    metrics = {}
    for k in k_values:
        metrics[f'hit_at_{k}'] = np.mean(hit_at_k_scores[f'hit_at_{k}']) if hit_at_k_scores[f'hit_at_{k}'] else 0.0
    metrics['mrr'] = np.mean(mrr_scores) if mrr_scores else 0.0

    return metrics

def main():
    """
    Main evaluation function.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Starting candidate generation evaluation")

    # Load test data
    test_data = load_test_data()

    # Initialize embeddings (dummy)
    user_embedding = UserEmbedding(embedding_dim=64)
    product_embedding = ProductEmbedding(embedding_dim=64)

    # Initialize candidate generators
    generators = [
        ("popularity", PopularityCandidateGenerator()),
        ("collaborative", CollaborativeCandidateGenerator()),
        ("content", ContentBasedCandidateGenerator()),
        ("embedding", EmbeddingBasedCandidateGenerator(user_embedding, product_embedding)),
    ]

    # Initialize hybrid candidate generator
    hybrid_generator = HybridCandidateGenerator(
        [gen for _, gen in generators],
        weights=[0.25, 0.25, 0.25, 0.25]  # Equal weights
    )
    generators.append(("hybrid", hybrid_generator))

    # Evaluate each generator
    all_results = {}

    for name, generator in generators:
        logger.info(f"Evaluating {name}")
        try:
            metrics = evaluate_candidate_generator(generator, test_data)
            all_results[name] = metrics
            logger.info(f"{name} metrics: {metrics}")
        except Exception as e:
            logger.error(f"Error evaluating {name}: {e}")
            all_results[name] = {"error": str(e)}

    # Save results
    output_dir = "./evaluation/reports/candidate_generation"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Evaluation results saved to {output_file}")

    # Also print summary
    print("\n=== Candidate Generation Evaluation Results ===")
    for name, metrics in all_results.items():
        if "error" not in metrics:
            print(f"{name}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value:.4f}")
        else:
            print(f"{name}: ERROR - {metrics['error']}")
        print()

if __name__ == "__main__":
    main()