"""
Model registry service for MLflow integration.
Provides abstraction over MLflow for model management.
"""
import mlflow
import mlflow.sklearn
import mlflow.pytorch
import mlflow.xgboost
import mlflow.lightgbm
from typing import Dict, Any, Optional, List
import logging
import os
from datetime import datetime
import json
import pickle
import numpy as np
from ..core.config import settings

logger = logging.getLogger(__name__)

class ModelRegistryService:
    def __init__(self, tracking_uri: str = None):
        """
        Initialize the model registry service.
        """
        self.tracking_uri = tracking_uri or settings.mlflow.TRACKING_URI
        if self.tracking_uri:
            mlflow.set_tracking_uri(self.tracking_uri)
        self.client = mlflow.tracking.MlflowClient()
        logger.info(f"Model registry initialized with tracking URI: {self.tracking_uri}")

    def get_model_version(self, model_name: str, version: str = None, stage: str = None) -> Dict[str, Any]:
        """
        Get a specific model version.
        """
        try:
            if version:
                model_version = self.client.get_model_version(name=model_name, version=version)
            elif stage:
                model_versions = self.client.get_latest_versions(name=model_name, stages=[stage])
                if not model_versions:
                    raise ValueError(f"No version of model {model_name} found in stage {stage}")
                model_version = model_versions[0]
            else:
                # Get latest version
                model_versions = self.client.get_latest_versions(name=model_name)
                if not model_versions:
                    raise ValueError(f"No versions found for model {model_name}")
                model_version = model_versions[0]

            # Get run data
            run = self.client.get_run(model_version.run_id)

            result = {
                "name": model_name,
                "version": model_version.version,
                "stage": model_version.current_stage,
                "model_uri": model_version.source,
                "run_id": model_version.run_id,
                "creation_timestamp": model_version.creation_timestamp,
                "last_updated_timestamp": model_version.last_updated_timestamp,
                "description": model_version.description,
                "tags": dict(model_version.tags),
                "parameters": dict(run.data.params),
                "metrics": dict(run.data.metrics),
                "artifact_uri": run.info.artifact_uri
            }

            return result
        except Exception as e:
            logger.error(f"Error getting model version for {model_name}: {e}")
            raise

    def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a model.
        """
        try:
            model_versions = self.client.get_model_version_by_name(model_name)
            versions = []
            for mv in model_versions:
                run = self.client.get_run(mv.run_id)
                versions.append({
                    "name": mv.name,
                    "version": mv.version,
                    "stage": mv.current_stage,
                    "creation_timestamp": mv.creation_timestamp,
                    "last_updated_timestamp": mv.last_updated_timestamp,
                    "description": mv.description,
                    "tags": dict(mv.tags),
                    "parameters": dict(run.data.params),
                    "metrics": dict(run.data.metrics)
                })
            return versions
        except Exception as e:
            logger.error(f"Error getting model versions for {model_name}: {e}")
            return []

    def transition_model_version_stage(self, model_name: str, version: str, stage: str) -> bool:
        """
        Transition a model version to a new stage.
        """
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=True
            )
            logger.info(f"Transitioned model {model_name} version {version} to stage {stage}")
            return True
        except Exception as e:
            logger.error(f"Error transitioning model {model_name} version {version} to stage {stage}: {e}")
            return False

    def get_model_by_alias(self, model_name: str, alias: str) -> Dict[str, Any]:
        """
        Get a model version by alias (e.g., 'production', 'staging').
        """
        try:
            model_version = self.client.get_model_version_by_alias(model_name, alias)
            run = self.client.get_run(model_version.run_id)

            result = {
                "name": model_name,
                "version": model_version.version,
                "stage": model_version.current_stage,
                "model_uri": model_version.source,
                "run_id": model_version.run_id,
                "creation_timestamp": model_version.creation_timestamp,
                "last_updated_timestamp": model_version.last_updated_timestamp,
                "description": model_version.description,
                "tags": dict(model_version.tags),
                "parameters": dict(run.data.params),
                "metrics": dict(run.data.metrics),
                "artifact_uri": run.info.artifact_uri,
                "alias": alias
            }

            return result
        except Exception as e:
            logger.error(f"Error getting model {model_name} by alias {alias}: {e}")
            raise

    def search_models(self, filter_string: str = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for models.
        """
        try:
            model_versions = self.client.search_model_versions(filter_string or "")
            models = []
            for mv in model_versions[:max_results]:
                try:
                    run = self.client.get_run(mv.run_id)
                    models.append({
                        "name": mv.name,
                        "version": mv.version,
                        "stage": mv.current_stage,
                        "creation_timestamp": mv.creation_timestamp,
                        "last_updated_timestamp": mv.last_updated_timestamp,
                        "description": mv.description,
                        "tags": dict(mv.tags),
                        "parameters": dict(run.data.params),
                        "metrics": dict(run.data.metrics)
                    })
                except Exception as e:
                    logger.warning(f"Could not get run data for model {mv.name} version {mv.version}: {e}")
                    # Still include basic info
                    models.append({
                        "name": mv.name,
                        "version": mv.version,
                        "stage": mv.current_stage,
                        "creation_timestamp": mv.creation_timestamp,
                        "last_updated_timestamp": mv.last_updated_timestamp,
                        "description": mv.description,
                        "tags": dict(mv.tags)
                    })
            return models
        except Exception as e:
            logger.error(f"Error searching models: {e}")
            return []

    def download_artifacts(self, model_name: str, version: str, artifact_path: str = None) -> str:
        """
        Download model artifacts.
        Returns local path to downloaded artifacts.
        """
        try:
            local_path = self.client.download_artifacts(
                run_id=self.get_model_version(model_name, version)["run_id"],
                path=artifact_path
            )
            logger.info(f"Downloaded artifacts for {model_name} version {version} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading artifacts for {model_name} version {version}: {e}")
            raise

    def log_model_metadata(self, model_name: str, version: str, metadata: Dict[str, Any]):
        """
        Log additional metadata for a model version.
        """
        try:
            model_version = self.get_model_version(model_name, version)
            run_id = model_version["run_id"]

            # Log metadata as tags
            for key, value in metadata.items():
                # MLflow tag values must be strings
                self.client.set_tag(run_id, key, str(value))

            logger.info(f"Logged metadata for {model_name} version {version}")
        except Exception as e:
            logger.error(f"Error logging metadata for {model_name} version {version}: {e}")
            raise

    def get_model_lineage(self, model_name: str, version: str) -> Dict[str, Any]:
        """
        Get model lineage information (dataset, feature, git commit, etc.).
        """
        try:
            model_version = self.get_model_version(model_name, version)
            run_id = model_version["run_id"]
            run = self.client.get_run(run_id)

            # Extract lineage information from tags/params
            lineage = {
                "model_name": model_name,
                "model_version": version,
                "dataset_version": run.data.params.get("dataset_version", "unknown"),
                "feature_version": run.data.params.get("feature_version", "unknown"),
                "git_commit": run.data.params.get("git_commit", "unknown"),
                "training_timestamp": run.data.params.get("training_timestamp", "unknown"),
                "environment_info": {
                    "python_version": run.data.params.get("python_version", "unknown"),
                    "mlflow_version": run.data.params.get("mlflow_version", "unknown")
                }
            }

            return lineage
        except Exception as e:
            logger.error(f"Error getting model lineage for {model_name} version {version}: {e}")
            return {
                "model_name": model_name,
                "model_version": version,
                "error": str(e)
            }

def get_model_registry_service() -> ModelRegistryService:
    """
    Factory function to get a model registry service instance.
    """
    return ModelRegistryService()