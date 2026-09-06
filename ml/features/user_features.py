"""
User feature extraction for the recommendation platform.
"""
import pandas as pd
import numpy as np
import os
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Cache for user features to avoid recomputing
_user_features_cache = None
_interactions_df = None

def _load_interactions_data() -> pd.DataFrame:
    """
    Load interactions data from CSV file.
    """
    global _interactions_df
    if _interactions_df is None:
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'interactions.csv')
        if not os.path.exists(csv_path):
            # Try current directory
            csv_path = 'interactions.csv'
        if os.path.exists(csv_path):
            logger.info(f"Loading interactions data from {csv_path}")
            _interactions_df = pd.read_csv(csv_path)
            # Ensure timestamp is datetime
            _interactions_df['timestamp'] = pd.to_datetime(_interactions_df['timestamp'])
        else:
            logger.warning("Interactions CSV not found; returning empty DataFrame")
            _interactions_df = pd.DataFrame()
    return _interactions_df

def get_user_features(user_id: Union[str, int]) -> Dict[str, Any]:
    """
    Get features for a user.
    Returns a dictionary of feature names to values.
    """
    interactions = _load_interactions_data()
    if interactions.empty:
        # Return default features
        return {
            "user_id": user_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_purchases": 0,
            "total_interactions": 0,
            "last_interaction_timestamp": None,
            "days_since_last_interaction": None,
            "view_to_click_ratio": 0.0,
            "purchase_rate": 0.0
        }

    # Convert user_id to string for comparison
    uid_str = str(user_id)
    # Filter interactions for this user
    user_interactions = interactions[
        interactions['user_id'].astype(str) == uid_str
    ]

    if user_interactions.empty:
        return {
            "user_id": user_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_purchases": 0,
            "total_interactions": 0,
            "last_interaction_timestamp": None,
            "days_since_last_interaction": None,
            "view_to_click_ratio": 0.0,
            "purchase_rate": 0.0
        }

    # Compute basic counts
    total_views = (user_interactions['event_type'] == 'view').sum()
    total_clicks = (user_interactions['event_type'] == 'click').sum()
    total_purchases = (user_interactions['event_type'] == 'purchase').sum()
    total_interactions = len(user_interactions)

    # Last interaction timestamp
    last_interaction = user_interactions['timestamp'].max()
    # Days since last interaction (assuming we want recency)
    now = pd.Timestamp.utcnow()
    days_since_last = (now - last_interaction).total_seconds() / (24 * 3600) if pd.notnull(last_interaction) else None

    # Ratios
    view_to_click_ratio = total_clicks / total_views if total_views > 0 else 0.0
    purchase_rate = total_purchases / total_interactions if total_interactions > 0 else 0.0

    features = {
        "user_id": user_id,
        "total_views": int(total_views),
        "total_clicks": int(total_clicks),
        "total_purchases": int(total_purchases),
        "total_interactions": int(total_interactions),
        "last_interaction_timestamp": last_interaction.isoformat() if pd.notnull(last_interaction) else None,
        "days_since_last_interaction": float(days_since_last) if days_since_last is not None else None,
        "view_to_click_ratio": float(view_to_click_ratio),
        "purchase_rate": float(purchase_rate)
    }

    return features

def get_user_feature_vector(user_id: Union[str, int]) -> np.ndarray:
    """
    Get user feature vector as a numpy array for use in ranking models.
    Order of features must match what the model expects.
    """
    features = get_user_features(user_id)
    # Define the order of features
    feature_order = [
        "total_views",
        "total_clicks",
        "total_purchases",
        "total_interactions",
        "days_since_last_interaction",
        "view_to_click_ratio",
        "purchase_rate"
    ]
    vector = []
    for fname in feature_order:
        val = features.get(fname)
        if val is None:
            # For missing datetime, use 0 or a large number
            val = 0.0
        vector.append(float(val))
    return np.array(vector, dtype=np.float32)

def get_all_user_features(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Get features for all users (or a limit) as a DataFrame.
    Useful for batch processing.
    """
    interactions = _load_interactions_data()
    if interactions.empty:
        return pd.DataFrame()

    # Get unique user IDs
    user_ids = interactions['user_id'].unique()
    if limit:
        user_ids = user_ids[:limit]

    features_list = []
    for uid in user_ids:
        features = get_user_features(uid)
        features_list.append(features)

    return pd.DataFrame(features_list)