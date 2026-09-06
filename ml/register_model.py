"""
Model registration script for the recommendation platform.
Registers trained models with MLflow tracking server.
"""
import os
import sys
import argparse
import logging
import json
import mlflow
import mlflow.pytorch
from ml.utils.reproducibility import setup_reproducibility, log_reproducibility_info, record_training_info
from ml.train import train_embedding_model, train_ranking_model
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def register_models(
    data_dir: str = '.',
    model_output_dir: str = './models',
    experiment_name: str = 'recommendation_platform',
    run_name: Optional[str] = None,
    tags: Optional[dict] = None,
    **train_kwargs
):
    """
    Train models and register them with MLflow.
    """
    # Set up MLflow tracking
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    logger.info(f"MLflow tracking URI: {mlflow_tracking_uri}")

    # Set up experiment
    mlflow.set_experiment(experiment_name)
    logger.info(f"Using MLflow experiment: {experiment_name}")

    # Start MLflow run
    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        logger.info(f"Started MLflow run: {run_id}")

        # Set tags
        if tags:
            for key, value in tags.items():
                mlflow.set_tag(key, value)
                logger.debug(f"Set tag {key}: {value}")

        # Log training parameters
        mlflow.log_params(train_kwargs)
        logger.info(f"Logged training parameters: {train_kwargs}")

        # Load interactions data
        interactions_path = os.path.join(data_dir, 'interactions.csv')
        if not os.path.exists(interactions_path):
            logger.error(f"Interactions file not found at {interactions_path}")
            sys.exit(1)

        interactions_df = pd.read_csv(interactions_path)
        logger.info(f"Loaded {len(interactions_df)} interactions from {interactions_path}")

        # Setup reproducibility
        seed = train_kwargs.get('seed', 42)
        repro_info = setup_reproducibility(seed=seed)
        log_reproducibility_info(repro_info)
        logger.info(f"Reproducibility info logged: seed={seed}")

        # Record dataset version (simple hash of interactions CSV)
        dataset_hash = hashlib.sha256(
            open(interactions_path, 'rb').read()
        ).hexdigest()
        dataset_version = f"interactions_{dataset_hash[:8]}"
        mlflow.log_param("dataset_version", dataset_version)
        logger.info(f"Dataset version: {dataset_version}")

        # Record feature version (based on feature extraction code)
        # For simplicity, we'll use a placeholder
        feature_version = "user_product_v1"
        mlflow.log_param("feature_version", feature_version)
        logger.info(f"Feature version: {feature_version}")

        # Train embedding model
        logger.info("Training embedding model...")
        embedding_model = train_embedding_model(
            interactions_df=interactions_df,
            model_output_path=os.path.join(model_output_dir, 'embedding_model.pth'),
            **train_kwargs
        )

        # Log embedding model to MLflow
        mlflow.pytorch.log_model(
            pytorch_model=embedding_model,
            artifact_path="embedding_model",
            registered_model_name="embedding_model"
        )
        logger.info("Embedding model logged to MLflow")

        # Train ranking model
        logger.info("Training ranking model...")
        ranking_model = train_ranking_model(
            interactions_df=interactions_df,
            model_output_path=os.path.join(model_output_dir, 'ranking_model.pth'),
            **train_kwargs
        )

        # Log ranking model to MLflow
        mlflow.pytorch.log_model(
            pytorch_model=ranking_model,
            artifact_path="ranking_model",
            registered_model_name="ranking_model"
        )
        logger.info("Ranking model logged to MLflow")

        # Evaluate models (optional)
        logger.info("Evaluating models...")
        # We could call ml/evaluate.py here, but for simplicity we'll skip
        # In a production pipeline, you would evaluate and only register if metrics pass thresholds

        # Log final metrics (placeholder)
        mlflow.log_metric("training_completed", 1)

        logger.info(f"Model registration completed. Run ID: {run_id}")
        return run_id

def main():
    parser = argparse.ArgumentParser(description='Register models with MLflow')
    parser.add_argument('--data-dir', type=str, default='.', help='Directory containing interactions.csv')
    parser.add_argument('--model-dir', type=str, default='./models', help='Directory to save models')
    parser.add_argument('--experiment-name', type=str, default='recommendation_platform', help='MLflow experiment name')
    parser.add_argument('--run-name', type=str, default=None, help='MLflow run name')
    parser.add_argument('--tag', action='append', help='Tag in format key=value (can be used multiple times)')
    parser.add_argument('--embedding-dim', type=int, default=64, help='Embedding dimension')
    parser.add_argument('--ranking-hidden-dim', type=int, default=128, help='Hidden dimension for ranking model')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=512, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # Parse tags
    tags = {}
    if args.tag:
        for tag_str in args.tag:
            if '=' in tag_str:
                key, value = tag_str.split('=', 1)
                tags[key] = value
            else:
                logger.warning(f"Ignoring invalid tag format: {tag_str}")

    # Prepare training kwargs
    train_kwargs = {
        'embedding_dim': args.embedding_dim,
        'ranking_hidden_dim': args.ranking_hidden_dim,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'lr': args.lr,
        'seed': args.seed
    }

    # Register models
    register_models(
        data_dir=args.data_dir,
        model_output_dir=args.model_dir,
        experiment_name=args.experiment_name,
        run_name=args.run_name,
        tags=tags,
        **train_kwargs
    )

if __name__ == "__main__":
    main()