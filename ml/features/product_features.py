"""
Product feature extraction for the recommendation platform.
"""
import pandas as pd
import numpy as np
import os
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Cache for product features
_product_features_cache = None
_interactions_df = None

def _load_interactions_data() -> pd.DataFrame:
    """
    Load interactions data from CSV file.
    """
    global _interactions_df
    if _interactions_df is None:
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'interactions.csv')
        if not os.path.exists(csv_path):
            csv_path = 'interactions.csv'
        if os.path.exists(csv_path):
            logger.info(f"Loading interactions data from {csv_path}")
            _interactions_df = pd.read_csv(csv_path)
            _interactions_df['timestamp'] = pd.to_datetime(_interactions_df['timestamp'])
        else:
            logger.warning("Interactions CSV not found; returning empty DataFrame")
            _interactions_df = pd.DataFrame()
    return _interactions_df

def get_product_features(product_id: Union[str, int]) -> Dict[str, Any]:
    """
    Get features for a product.
    Returns a dictionary of feature names to values.
    """
    interactions = _load_interactions_data()
    if interactions.empty:
        return {
            "product_id": product_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_purchases": 0,
            "total_interactions": 0,
            "last_interaction_timestamp": None,
            "days_since_last_interaction": None,
            "view_to_click_ratio": 0.0,
            "purchase_rate": 0.0
        }

    pid_str = str(product_id)
    product_interactions = interactions[
        interactions['product_id'].astype(str) == pid_str
    ]

    if product_interactions.empty:
        return {
            "product_id": product_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_purchases": 0,
            "total_interactions": 0,
            "last_interaction_timestamp": None,
            "days_since_last_interaction": None,
            "view_to_click_ratio": 0.0,
            "purchase_rate": 0.0
        }

    total_views = (product_interactions['event_type'] == 'view').sum()
    total_clicks = (product_interactions['event_type'] == 'click').sum()
    total_purchases = (product_interactions['event_type'] == 'purchase').sum()
    total_interactions = len(product_interactions)

    last_interaction = product_interactions['timestamp'].max()
    now = pd.Timestamp.utcnow()
    days_since_last = (now - last_interaction).total_seconds() / (24 * 3600) if pd.notnull(last_interaction) else None

    view_to_click_ratio = total_clicks / total_views if total_views > 0 else 0.0
    purchase_rate = total_purchases / total_interactions if total_interactions > 0 else 0.0

    features = {
        "product_id": product_id,
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

def get_product_feature_vector(product_id: Union[str, int]) -> np.ndarray:
    """
    Get product feature vector as a numpy array for use in ranking models.
    """
    features = get_product_features(product_id)
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
            val = 0.0
        vector.append(float(val))
    return np.array(vector, dtype=np.float32)

def get_all_product_features(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Get features for all products (or a limit) as a DataFrame.
    """
    interactions = _load_interactions_data()
    if interactions.empty:
        return pd.DataFrame()

    product_ids = interactions['product_id'].unique()
    if limit:
        product_ids = product_ids[:limit]

    features_list = []
    for pid in product_ids:
        features = get_product_features(pid)
        features_list.append(features)

    return pd.DataFrame(features_list)