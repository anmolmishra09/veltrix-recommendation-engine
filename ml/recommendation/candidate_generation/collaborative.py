"""
Collaborative filtering candidate generator.
"""
import pandas as pd
import numpy as np
from .base import CandidateGenerator, Candidate
import logging
from typing import List, Tuple, Any, Optional, Union, Dict
import itertools

logger = logging.getLogger(__name__)

class CollaborativeCandidateGenerator(CandidateGenerator):
    def __init__(self, item_similarity_df: pd.DataFrame = None, user_item_matrix: pd.DataFrame = None):
        """
        Initialize the collaborative filtering candidate generator.

        Args:
            item_similarity_df: DataFrame with columns ['item_id_1', 'item_id_2', 'similarity'].
                                If provided, will be used to get similar items based on collaborative filtering.
            user_item_matrix: DataFrame with users as rows and items as columns (interaction counts or ratings).
                              If provided, we can compute item similarities on the fly.
        """
        super().__init__("collaborative")
        self.item_similarity_df = item_similarity_df
        self.user_item_matrix = user_item_matrix
        self.item_id_to_index = {}
        self.similarity_matrix = None

        if item_similarity_df is not None:
            self._build_similarity_lookup()
        elif user_item_matrix is not None:
            self._build_similarity_from_matrix()
        else:
            logger.warning("No similarity data or user-item matrix provided. Collaborative generator will return empty candidates.")

    def _build_similarity_lookup(self):
        """Build a similarity lookup from the similarity dataframe."""
        if self.item_similarity_df is None:
            logger.warning("Item similarity dataframe is not provided.")
            return

        required_columns = ['item_id_1', 'item_id_2', 'similarity']
        for col in required_columns:
            if col not in self.item_similarity_df.columns:
                raise ValueError(f"Item similarity dataframe must have column '{col}'")

        # Create a dictionary mapping item_id to a list of (similar_item_id, similarity)
        self.item_similarity_lookup = {}
        for _, row in self.item_similarity_df.iterrows():
            id1 = str(row['item_id_1'])
            id2 = str(row['item_id_2'])
            sim = row['similarity']

            if id1 not in self.item_similarity_lookup:
                self.item_similarity_lookup[id1] = []
            self.item_similarity_lookup[id1].append((id2, sim))

            if id2 not in self.item_similarity_lookup:
                self.item_similarity_lookup[id2] = []
            self.item_similarity_lookup[id2].append((id1, sim))

        # Sort each list by similarity descending
        for item_id in self.item_similarity_lookup:
            self.item_similarity_lookup[item_id].sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Built collaborative similarity lookup for {len(self.item_similarity_lookup)} items")

    def _build_similarity_from_matrix(self):
        """Build item similarity matrix from user-item matrix using cosine similarity."""
        if self.user_item_matrix is None:
            logger.warning("User-item matrix is not provided.")
            return

        # Assume first column is user_id, the rest are item IDs
        user_column = self.user_item_matrix.columns[0]
        item_columns = [col for col in self.user_item_matrix.columns if col != user_column]

        # Convert to numpy array (users x items)
        matrix = self.user_item_matrix[item_columns].values.astype(np.float32)

        # Compute item-item similarity (cosine similarity)
        # We'll transpose to get items x users
        item_vectors = matrix.T  # Shape (n_items, n_users)
        norms = np.linalg.norm(item_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-8
        normalized_vectors = item_vectors / norms

        self.similarity_matrix = np.dot(normalized_vectors, normalized_vectors.T)  # Shape (n_items, n_items)

        # Create ID to index mapping for items
        self.item_id_to_index = {str(id_val): idx for idx, id_val in enumerate(item_columns)}
        self.index_to_item_id = {idx: str(id_val) for idx, id_val in enumerate(item_columns)}

        logger.info(f"Built collaborative similarity matrix from user-item matrix for {len(self.item_id_to_index)} items")

    def _get_similar_items(self, item_id: Any, top_k: int = 100) -> List[Tuple[Any, float]]:
        """
        Get similar items for a given item ID based on collaborative filtering.

        Args:
            item_id: The item ID.
            top_k: Number of similar items to return.

        Returns:
            List of tuples (item_id, similarity) sorted by similarity descending.
        """
        item_id_str = str(item_id)

        if hasattr(self, 'item_similarity_lookup'):
            # Use precomputed similarity lookup
            if item_id_str not in self.item_similarity_lookup:
                logger.warning(f"Item ID {item_id_str} not found in similarity lookup.")
                return []
            similar_items = self.item_similarity_lookup[item_id_str]
            return similar_items[:top_k]
        elif self.similarity_matrix is not None and hasattr(self, 'item_id_to_index'):
            # Use similarity matrix from user-item matrix
            if item_id_str not in self.item_id_to_index:
                logger.warning(f"Item ID {item_id_str} not found in item index.")
                return []
            idx = self.item_id_to_index[item_id_str]
            similarities = self.similarity_matrix[idx]
            # Get indices of top similar items (excluding itself)
            similar_indices = np.argsort(similarities)[::-1][1:top_k+1]  # Exclude self
            similar_items = []
            for sim_idx in similar_indices:
                similar_item_id = self.index_to_item_id[sim_idx]
                similarity = similarities[sim_idx]
                similar_items.append((similar_item_id, similarity))
            return similar_items
        else:
            logger.warning("No similarity data available.")
            return []

    def generate(self, user_id: Any, context: dict = None, limit: int = 100, user_history: List[Any] = None) -> List[Candidate]:
        """
        Generate candidates based on collaborative filtering (items similar to those the user has interacted with).

        Args:
            user_id: The ID of the user.
            context: Additional context (not used).
            limit: Maximum number of candidates to generate.
            user_history: List of item IDs that the user has interacted with (past interactions).
                          If not provided, the generator cannot generate candidates.

        Returns:
            List of Candidate objects.
        """
        if user_history is None or len(user_history) == 0:
            logger.warning("User history is empty. Cannot generate collaborative candidates.")
            return []

        # For each item in user history, get similar items and aggregate scores
        candidate_scores = {}

        for item_id in user_history:
            similar_items = self._get_similar_items(item_id, top_k=limit)
            for sim_item_id, similarity in similar_items:
                if sim_item_id not in candidate_scores:
                    candidate_scores[sim_item_id] = 0.0
                candidate_scores[sim_item_id] += similarity  # Simple aggregation: sum of similarities

        # Sort candidates by score descending
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

        # Take top 'limit'
        top_candidates = sorted_candidates[:limit]

        item_ids = [item[0] for item in top_candidates]
        scores = [item[1] for item in top_candidates]

        return self._to_candidate_list(item_ids, scores)