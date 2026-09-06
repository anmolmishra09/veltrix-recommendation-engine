"""
Feature generation script for product features (Pandas version).
Reads processed interaction data, generates product features, and saves to features directory.
"""
import pandas as pd
import numpy as np
import os
import logging
from typing import Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def generate_product_features(df: pd.DataFrame,
                              window_days: int = 30,
                              end_date: Union[str, pd.Timestamp] = None) -> pd.DataFrame:
    """
    Generate product features from interaction data.

    Features:
    - total_views, total_clicks, total_purchases, total_add_to_cart, etc.
    - views_last_7d, clicks_last_7d, purchases_last_7d (rolling window)
    - conversion_rate (purchases / views)
    - click_through_rate (clicks / views)
    - etc.

    Args:
        df: Processed interaction dataframe (must have user_id, product_id, event_type, timestamp).
        window_days: Number of days for the rolling window features.
        end_date: The end date for the window. If None, uses the max timestamp in the data.

    Returns:
        DataFrame with product_id as index and feature columns.
    """
    # Make a copy
    df = df.copy()

    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Determine end_date for windowing
    if end_date is None:
        end_date = df['timestamp'].max()
    else:
        end_date = pd.to_datetime(end_date)

    start_date = end_date - timedelta(days=window_days)

    # Split data into historical and window
    historical_df = df[df['timestamp'] <= end_date]
    window_df = historical_df[historical_df['timestamp'] >= start_date]

    # Define event types we want to count
    event_types = ['view', 'click', 'purchase', 'add_to_cart', 'like', 'wishlist', 'search', 'impression']

    # Initialize features DataFrame
    product_ids = historical_df['product_id'].unique()
    features_list = []

    for product_id in product_ids:
        product_hist = historical_df[historical_df['product_id'] == product_id]
        product_window = window_df[window_df['product_id'] == product_id]

        product_features = {'product_id': product_id}

        # Historical counts
        for event_type in event_types:
            count = (product_hist['event_type'] == event_type).sum()
            product_features[f'total_{event_type}'] = count

        # Window counts
        for event_type in event_types:
            count = (product_window['event_type'] == event_type).sum()
            product_features[f'{event_type}_last_{window_days}d'] = count

        # Calculate rates (avoid division by zero)
        views = product_features['total_view']
        clicks = product_features['total_click']
        purchases = product_features['total_purchase']

        product_features['click_through_rate'] = clicks / views if views > 0 else 0.0
        product_features['conversion_rate'] = purchases / views if views > 0 else 0.0
        product_features['add_to_cart_rate'] = product_features['total_add_to_cart'] / views if views > 0 else 0.0

        # Recency: days since last interaction
        if len(product_hist) > 0:
            last_interaction = product_hist['timestamp'].max()
            days_since_last = (end_date - last_interaction).days
            product_features['days_since_last_interaction'] = max(days_since_last, 0)
        else:
            product_features['days_since_last_interaction'] = window_days  # If no interaction in history, set to window

        # Total interactions
        product_features['total_interactions'] = len(product_hist)
        product_features[f'interactions_last_{window_days}d'] = len(product_window)

        # Ratio of interactions in window (if total_interactions > 0)
        if product_features['total_interactions'] > 0:
            product_features[f'interaction_ratio_last_{window_days}d'] = product_features[f'interactions_last_{window_days}d'] / product_features['total_interactions']
        else:
            product_features[f'interaction_ratio_last_{window_days}d'] = 0.0

        features_list.append(product_features)

    # Create DataFrame
    features_df = pd.DataFrame(features_list)
    features_df.set_index('product_id', inplace=True)

    # Fill NaN with 0 (for products who had no interactions in the window)
    features_df = features_df.fillna(0)

    return features_df

def process_file(input_file: str, output_file: str, window_days: int = 30):
    """
    Process a single CSV file of interactions to generate product features.

    Args:
        input_file: Path to the processed CSV file.
        output_file: Path to save the product features CSV file.
        window_days: Number of days for the rolling window features.
    """
    logger.info(f"Reading processed data from {input_file}")
    df = pd.read_csv(input_file)

    logger.info(f"Generating product features with window of {window_days} days")
    features_df = generate_product_features(df, window_days=window_days)

    logger.info(f"Saving product features to {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    features_df.to_csv(output_file)

    logger.info(f"Generated features for {len(features_df)} products")

def process_directory(input_dir: str, output_dir: str, window_days: int = 30):
    """
    Process all CSV files in a directory.

    Args:
        input_dir: Directory containing processed CSV files.
        output_dir: Directory to save product features CSV files.
    """
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            process_file(input_file, output_file, window_days)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Process the interactions data
    input_dir = "data/processed"
    output_dir = "data/features"

    logger.info("Starting product feature generation")
    process_directory(input_dir, output_dir, window_days=30)
    logger.info("Product feature generation completed")