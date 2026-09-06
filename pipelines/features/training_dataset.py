"""
Training dataset generation script.
Creates training data for ranking models from processed interactions and features.
"""
import pandas as pd
import numpy as np
import os
import logging
from typing import Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def generate_training_dataset(interactions_df: pd.DataFrame,
                              user_features_df: pd.DataFrame = None,
                              product_features_df: pd.DataFrame = None,
                              window_days: int = 30,
                              test_size: float = 0.2) -> dict:
    """
    Generate training dataset for ranking models.

    Args:
        interactions_df: Processed interaction data.
        user_features_df: User features dataframe (optional).
        product_features_df: Product features dataframe (optional).
        window_days: Window for feature calculation.
        test_size: Fraction of data to use for testing.

    Returns:
        Dictionary with keys: 'X_train', 'X_test', 'y_train', 'y_test', 'feature_names'
    """
    logger.info("Generating training dataset")

    # Make a copy
    df = interactions_df.copy()

    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Determine end_date for windowing
    end_date = df['timestamp'].max()
    start_date = end_date - timedelta(days=window_days)

    # Split data into historical and window
    historical_df = df[df['timestamp'] <= end_date]
    window_df = historical_df[historical_df['timestamp'] >= start_date]

    # We'll create training examples from interactions in the window
    # For each interaction, we'll create a feature vector combining user and product features
    # The target will be based on the event type (e.g., purchase=1, view=0, or we can use weighted scores)

    # Define positive interactions (we'll consider purchase as positive for simplicity)
    positive_events = ['purchase', 'add_to_cart']  # These indicate strong interest
    window_df['label'] = window_df['event_type'].apply(lambda x: 1 if x in positive_events else 0)

    # If we don't have enough positive examples, we can also weight by event type
    # For now, we'll use binary labels

    # Prepare features
    # We'll create feature vectors for each (user_id, product_id) pair in the window data

    # Get unique user and product IDs from window data
    user_ids = window_df['user_id'].unique()
    product_ids = window_df['product_id'].unique()

    # If we have user and product features, we'll use them
    # Otherwise, we'll create simple features from the interaction data

    feature_vectors = []
    labels = []

    for _, row in window_df.iterrows():
        user_id = row['user_id']
        product_id = row['product_id']
        label = row['label']

        # Start with basic features
        features = []

        # User features (if available)
        if user_features_df is not None and user_id in user_features_df.index:
            user_feat = user_features_df.loc[user_id].values
            features.extend(user_feat)
        else:
            # Default user features (zeros)
            # We'll need to know the size - for now, we'll use a default size
            # In a real implementation, we'd get this from the feature store
            pass

        # Product features (if available)
        if product_features_df is not None and product_id in product_features_df.index:
            product_feat = product_features_df.loc[product_id].values
            features.extend(product_feat)
        else:
            # Default product features (zeros)
            pass

        # Interaction-specific features
        # Time since last interaction for this user-product pair
        # We'll skip this for simplicity in this example

        # Event type features (one-hot encoded)
        event_type = row['event_type']
        event_types = ['view', 'click', 'purchase', 'add_to_cart', 'like', 'wishlist', 'search', 'impression']
        event_features = [1.0 if event_type == et else 0.0 for et in event_types]
        features.extend(event_features)

        # Context features (if available)
        # We'll skip for now

        feature_vectors.append(features)
        labels.append(label)

    # Convert to numpy arrays
    X = np.array(feature_vectors, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)

    # Split into train and test
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # Generate feature names (placeholder)
    # In a real implementation, we'd get actual feature names from the feature store
    n_features = X.shape[1]
    feature_names = [f"feature_{i}" for i in range(n_features)]

    result = {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'feature_names': feature_names
    }

    logger.info(f"Generated training dataset: {X_train.shape[0]} train samples, {X_test.shape[0]} test samples")
    return result

def save_training_dataset(dataset_dict: dict, output_dir: str):
    """
    Save the training dataset to files.

    Args:
        dataset_dict: Dictionary from generate_training_dataset.
        output_dir: Directory to save the files.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save as numpy arrays
    np.save(os.path.join(output_dir, 'X_train.npy'), dataset_dict['X_train'])
    np.save(os.path.join(output_dir, 'X_test.npy'), dataset_dict['X_test'])
    np.save(os.path.join(output_dir, 'y_train.npy'), dataset_dict['y_train'])
    np.save(os.path.join(output_dir, 'y_test.npy'), dataset_dict['y_test'])

    # Save feature names
    import json
    with open(os.path.join(output_dir, 'feature_names.json'), 'w') as f:
        json.dump(dataset_dict['feature_names'], f)

    logger.info(f"Saved training dataset to {output_dir}")

def process_from_files(interactions_file: str,
                       user_features_file: str = None,
                       product_features_file: str = None,
                       output_dir: str = "./data/training_dataset",
                       window_days: int = 30,
                       test_size: float = 0.2):
    """
    Generate training dataset from CSV files.

    Args:
        interactions_file: Path to processed interactions CSV.
        user_features_file: Path to user features CSV (optional).
        product_features_file: Path to product features CSV (optional).
        output_dir: Directory to save training dataset.
        window_days: Window for feature calculation.
        test_size: Fraction of data to use for testing.
    """
    logger.info("Loading data from files")

    # Load interactions
    interactions_df = pd.read_csv(interactions_file)
    logger.info(f"Loaded {len(interactions_df)} interactions")

    # Load user features if provided
    user_features_df = None
    if user_features_file and os.path.exists(user_features_file):
        user_features_df = pd.read_csv(user_features_file)
        # Assume first column is user_id
        id_column = user_features_df.columns[0]
        user_features_df.set_index(id_column, inplace=True)
        logger.info(f"Loaded user features for {len(user_features_df)} users")

    # Load product features if provided
    product_features_df = None
    if product_features_file and os.path.exists(product_features_file):
        product_features_df = pd.read_csv(product_features_file)
        # Assume first column is product_id
        id_column = product_features_df.columns[0]
        product_features_df.set_index(id_column, inplace=True)
        logger.info(f"Loaded product features for {len(product_features_df)} products")

    # Generate training dataset
    dataset = generate_training_dataset(
        interactions_df=interactions_df,
        user_features_df=user_features_df,
        product_features_df=product_features_df,
        window_days=window_days,
        test_size=test_size
    )

    # Save dataset
    save_training_dataset(dataset, output_dir)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Example usage - in practice, these would be configured via command line args or config
    interactions_file = "data/processed/interactions.csv"  # Adjust as needed
    user_features_file = "data/features/user_features.csv"
    product_features_file = "data/features/product_features.csv"
    output_dir = "data/training_dataset"

    # Check if files exist, if not, create dummy data for demonstration
    if not os.path.exists(interactions_file):
        logger.warning(f"Interactions file {interactions_file} not found. Creating dummy data.")
        # Create dummy interactions data
        dummy_interactions = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(1, 101)] * 10,
            'product_id': [f'product_{i}' for i in range(1, 51)] * 10,
            'event_type': np.random.choice(['view', 'click', 'purchase', 'add_to_cart'], size=1000),
            'timestamp': pd.date_range('2026-09-01', periods=1000, freq='H'),
            'session_id': [f'session_{i}' for i in range(1000)],
            'context': ['{}'] * 1000,
            'metadata': ['{}'] * 1000
        })
        os.makedirs(os.path.dirname(interactions_file), exist_ok=True)
        dummy_interactions.to_csv(interactions_file, index=False)
        interactions_df = dummy_interactions
    else:
        interactions_df = pd.read_csv(interactions_file)

    # Generate dummy feature files if they don't exist
    if not os.path.exists(user_features_file):
        logger.warning(f"User features file {user_features_file} not found. Creating dummy data.")
        dummy_user_features = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(1, 101)],
            'feat_0': np.random.rand(100),
            'feat_1': np.random.rand(100),
            'feat_2': np.random.rand(100)
        })
        os.makedirs(os.path.dirname(user_features_file), exist_ok=True)
        dummy_user_features.to_csv(user_features_file, index=False)

    if not os.path.exists(product_features_file):
        logger.warning(f"Product features file {product_features_file} not found. Creating dummy data.")
        dummy_product_features = pd.DataFrame({
            'product_id': [f'product_{i}' for i in range(1, 51)],
            'feat_0': np.random.rand(50),
            'feat_1': np.random.rand(50),
            'feat_2': np.random.rand(50)
        })
        os.makedirs(os.path.dirname(product_features_file), exist_ok=True)
        dummy_product_features.to_csv(product_features_file, index=False)

    # Process the data
    process_from_files(
        interactions_file=interactions_file,
        user_features_file=user_features_file,
        product_features_file=product_features_file,
        output_dir=output_dir,
        window_days=30,
        test_size=0.2
    )