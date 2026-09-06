"""
Similarity metrics for embeddings.
"""
import numpy as np
from typing import Union

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Cosine similarity as a float.
    """
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)

def cosine_similarity_batch(vec1: np.ndarray, vec2_matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a vector and a matrix of vectors.

    Args:
        vec1: Vector of shape (d,).
        vec2_matrix: Matrix of shape (n, d).

    Returns:
        Array of shape (n,) with cosine similarities.
    """
    # Ensure vec1 is 2D for broadcasting
    vec1 = vec1.reshape(1, -1)
    dot_product = np.dot(vec1, vec2_matrix.T)  # Shape (1, n)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2_matrix, axis=1)  # Shape (n,)
    # Avoid division by zero
    norm_vec2[norm_vec2 == 0] = 1e-8
    similarities = dot_product / (norm_vec1 * norm_vec2.reshape(1, -1))
    return similarities.flatten()

def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute Euclidean distance between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Euclidean distance.
    """
    return np.linalg.norm(vec1 - vec2)

def pairwise_cosine_similarity(matrix: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity for a matrix of vectors.

    Args:
        matrix: Matrix of shape (n, d).

    Returns:
        Matrix of shape (n, n) with cosine similarities.
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    normalized = matrix / norms
    similarity_matrix = np.dot(normalized, normalized.T)
    return similarity_matrix