"""
Popularity-based candidate generator.
"""
import pandas as pd
import numpy as np
from .base import CandidateGenerator, Candidate
import logging
from typing import List, Tuple, Any, Optional, Union

logger = logging.getLogger(__name__)

class PopularityCandidateGenerator(CandidateGenerator):
    def __init__(self, popularity_df: pd.DataFrame = None, popularity_column: str = 'popularity_score'):
        """
        Initialize the popularity candidate generator.

        Args:
            popularity_df: DataFrame with columns ['item_id', 'popularity_score'].
                           If None, the generator will not be able to generate candidates until fitted.
            popularity_column: Name of the column in popularity_df that contains the popularity score.
        """
        super().__init__("popularity")
        self.popularity_df = popularity_df
        self.popularity_column = popularity_column
        self.item_id_to_popularity = {}

        if popularity_df is not None:
            self._build_lookup()

    def _build_lookup(self):
        """Build a lookup dictionary from item_id to popularity score."""
        if self.popularity_df is None:
            logger.warning("Popularity dataframe is not provided. Lookup will be empty.")
            return

        # Ensure we have the required columns
        if 'item_id' not in self.popularity_df.columns:
            raise ValueError("Popularity dataframe must have an 'item_id' column")
        if self.popularity_column not in self.popularity_df.columns:
            raise ValueError(f"Popularity dataframe must have a '{self.popularity_column}' column")

        # Create lookup dictionary
        self.item_id_to_popularity = dict(zip(
            self.popularity_df['item_id'].astype(str),
            self.popularity_df[self.popularity_column]
        ))
        logger.info(f"Built popularity lookup for {len(self.item_id_to_popularity)} items")

    def fit(self, interactions_df: pd.DataFrame, time_decay_days: int = 30, popularity_column: str = None):
        """
        Fit the popularity model from interaction data.

        Args:
            interactions_df: DataFrame with columns ['user_id', 'item_id', 'event_type', 'timestamp'].
            time_decay_days: Half-life for time decay in days. Events more recent get higher weight.
            popularity_column: Name of the popularity column to use. If None, uses the instance's popularity_column.
        """
        if popularity_column is not None:
            self.popularity_column = popularity_column

        # Ensure timestamp is datetime
        interactions_df = interactions_df.copy()
        interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])

        # Compute time decay weights
        now = interactions_df['timestamp'].max()
        interactions_df['days_ago'] = (now - interactions_df['timestamp']).dt.total_seconds() / (24 * 3600)
        # Weight = exp(-lambda * days_ago), where lambda = ln(2) / half_life
        lambda_val = np.log(2) / time_decay_days
        interactions_df['weight'] = np.exp(-lambda_val * interactions_df['days_ago'])

        # We can also weight by event type (e.g., purchase > view)
        event_type_weights = {
            'purchase': 3.0,
            'add_to_cart': 2.0,
            'view': 1.0,
            'click': 1.5,
            'like': 1.0,
            'wishlist': 1.0,
            'search': 0.5,
            'impression': 0.1
        }
        interactions_df['event_type_weight'] = interactions_df['event_type'].map(event_type_weights).fillna(1.0)

        # Combined weight
        interactions_df['combined_weight'] = interactions_df['weight'] * interactions_df['event_type_weight']

        # Aggregate by item_id
        popularity = interactions_df.groupby('item_id')['combined_weight'].sum().reset_index()
        popularity.columns = ['item_id', self.popularity_column]

        self.popularity_df = popularity
        self._build_lookup()

        logger.info(f"Fitted popularity model on {len(interactions_df)} interactions")

    def generate(self, user_id: Any, context: dict = None, limit: int = 100) -> List[Candidate]:
        """
        Generate candidates based on popularity.

        Args:
            user_id: The ID of the user (not used in popularity, but kept for interface consistency).
            context: Additional context (not used).
            limit: Maximum number of candidates to generate.

        Returns:
            List of Candidate objects sorted by popularity descending.
        """
        if not self.item_id_to_popularity:
            logger.warning("Popularity lookup is empty. Returning empty candidate list.")
            return []

        # Sort items by popularity descending
        sorted_items = sorted(self.item_id_to_popularity.items(), key=lambda x: x[1], reverse=True)

        # Take top 'limit' items
        top_items = sorted_items[:limit]

        item_ids = [item[0] for item in top_items]
        scores = [item[1] for item in top_items]

        return self._to_candidate_list(item_ids, scores)

    def update_popularity(self, new_popularity_df: pd.DataFrame):
        """
        Update the popularity lookup with a new dataframe.

        Args:
            new_popularity_df: New popularity dataframe.
        """
        self.popularity_df = new_popularity_df
        self._build_lookup()