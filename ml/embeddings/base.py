"""
Base class for embeddings.
"""
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseEmbedding(ABC):
    def __init__(self):
        self.embedding_dim = None
        self._embeddings = None  # Will be a numpy array or a dict mapping id to vector
        self.id_to_index = {}    # Mapping from ID to index in the embeddings array
        self.index_to_id = {}    # Mapping from index to ID

    @abstractmethod
    def load(self, path: str):
        """
        Load embeddings from a file or database.

        Args:
            path: Path to the embeddings file or connection string.
        """
        pass

    @abstractmethod
    def get_embedding(self, id: Union[str, int]) -> np.ndarray:
        """
        Get the embedding vector for a given ID.

        Args:
            id: The ID of the item (user or product).

        Returns:
            Embedding vector as a numpy array.
        """
        pass

    @abstractmethod
    def get_embeddings(self, ids: List[Union[str, int]]) -> np.ndarray:
        """
        Get embedding vectors for a list of IDs.

        Args:
            ids: List of IDs.

        Returns:
            Matrix of shape (len(ids), embedding_dim).
        """
        pass

    def similarity(self, id1: Union[str, int], id2: Union[str, int]) -> float:
        """
        Compute similarity between two IDs.

        Args:
            id1: First ID.
            id2: Second ID.

        Returns:
            Similarity score.
        """
        vec1 = self.get_embedding(id1)
        vec2 = self.get_embedding(id2)
        from .similarity import cosine_similarity
        return cosine_similarity(vec1, vec2)

    def most_similar(self, id: Union[str, int], top_k: int = 10, exclude_id: bool = True) -> List[tuple]:
        """
        Find the most similar IDs to a given ID.

        Args:
            id: The ID to find similarities for.
            top_k: Number of similar items to return.
            exclude_id: Whether to exclude the input ID from the results.

        Returns:
            List of tuples (ID, similarity_score) sorted by similarity in descending order.
        """
        target_vec = self.get_embedding(id)
        all_ids = list(self.id_to_index.keys())
        all_vecs = self.get_embeddings(all_ids)

        from .similarity import cosine_similarity_batch
        similarities = cosine_similarity_batch(target_vec, all_vecs)

        # Create list of (id, similarity)
        id_similarity = list(zip(all_ids, similarities))

        # Sort by similarity descending
        id_similarity.sort(key=lambda x: x[1], reverse=True)

        # Exclude the input ID if requested
        if exclude_id:
            id_similarity = [pair for pair in id_similarity if pair[0] != id]

        # Return top_k
        return id_similarity[:top_k]