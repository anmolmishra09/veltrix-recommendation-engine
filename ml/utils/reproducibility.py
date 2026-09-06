"""
Utilities for ensuring reproducibility in machine learning experiments.
"""
import os
import json
import yaml
import hashlib
import platform
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
import mlflow
from .seed import set_seed, get_seed


def setup_reproducibility(seed: int = 42) -> Dict[str, Any]:
    """
    Setup reproducibility for an experiment and return reproduction info.

    Args:
        seed: Random seed to use

    Returns:
        Dictionary containing reproducibility information
    """
    # Set the seed
    set_seed(seed)

    # Collect environment information
    env_info = _get_environment_info()

    # Create reproducibility info
    repro_info = {
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": env_info,
        "dependencies": _get_dependency_versions(),
    }

    return repro_info


def log_reproducibility_info(repro_info: Dict[str, Any]) -> None:
    """
    Log reproducibility information to MLflow.

    Args:
        repro_info: Reproducibility information dictionary
    """
    # Log seed as parameter
    mlflow.log_param("random_seed", repro_info["seed"])

    # Log environment information as tags
    for key, value in repro_info["environment"].items():
        # MLflow tag values must be strings
        mlflow.set_tag(f"env_{key}", str(value))

    # Log dependency information
    for dep, version in repro_info["dependencies"].items():
        mlflow.set_tag(f"dep_{dep}", version)

    # Save reproducibility info as artifact
    os.makedirs("tmp/reproducibility", exist_ok=True)
    with open("tmp/reproducibility/reproducibility_info.json", "w") as f:
        json.dump(repro_info, f, indent=2)
    mlflow.log_artifact("tmp/reproducibility/reproducibility_info.json", "reproducibility")


def record_training_info(
    dataset_version: str,
    feature_version: str,
    model_params: Dict[str, Any],
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record training information for reproducibility.

    Args:
        dataset_version: Version identifier for the dataset
        feature_version: Version identifier for the feature set
        model_params: Model parameters used for training
        additional_info: Additional information to record

    Returns:
        Dictionary containing training information
    """
    train_info = {
        "dataset_version": dataset_version,
        "feature_version": feature_version,
        "model_parameters": model_params,
        "random_seed": get_seed(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if additional_info:
        train_info.update(additional_info)

    # Log to MLflow
    mlflow.log_param("dataset_version", dataset_version)
    mlflow.log_param("feature_version", feature_version)
    for param_name, param_value in model_params.items():
        mlflow.log_param(f"model_{param_name}", param_value)

    return train_info


def get_git_info() -> Dict[str, str]:
    """
    Get git repository information.

    Returns:
        Dictionary with git information
    """
    git_info = {}
    try:
        # Get current commit hash
        git_info["commit_hash"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip()

        # Get current branch
        git_info["branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        ).decode("utf-8").strip()

        # Get commit message
        git_info["commit_message"] = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%s"]
        ).decode("utf-8").strip()

        # Check if there are uncommitted changes
        diff_output = subprocess.check_output(
            ["git", "diff", "--shortstat"]
        ).decode("utf-8").strip()
        git_info["has_uncommitted_changes"] = len(diff_output) > 0

    except (subprocess.CalledProcessError, FileNotFoundError):
        git_info["error"] = "Unable to get git information"

    return git_info


def _get_environment_info() -> Dict[str, Any]:
    """
    Get information about the runtime environment.

    Returns:
        Dictionary containing environment information
    """
    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "system": platform.system(),
        "processor": platform.processor(),
    }

    # Add CUDA information if available
    try:
        import torch
        env_info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            env_info["cuda_version"] = torch.version.cuda
            env_info["gpu_count"] = torch.cuda.device_count()
            env_info["gpu_names"] = [
                torch.cuda.get_device_name(i)
                for i in range(torch.cuda.device_count())
            ]
    except ImportError:
        pass

    try:
        import tensorflow as tf
        env_info["tensorflow_version"] = tf.__version__
        # Check for GPU availability in TensorFlow
        gpus = tf.config.list_physical_devices('GPU')
        env_info["tf_gpu_available"] = len(gpus) > 0
        if gpus:
            env_info["tf_gpu_names"] = [gpu.name for gpu in gpus]
    except ImportError:
        pass

    # Add git information
    env_info.update(get_git_info())

    return env_info


def _get_dependency_versions() -> Dict[str, str]:
    """
    Get versions of key dependencies.

    Returns:
        Dictionary mapping package names to versions
    """
    dependencies = {}

    # Common ML/data science packages
    packages = [
        "numpy",
        "pandas",
        "scikit-learn",
        "torch",
        "tensorflow",
        "mlflow",
        "feast",
        "redis",
        "psycopg2-binary",
        "fastapi",
        "uvicorn",
        "prometheus-client",
        "opentelemetry-api",
    ]

    for package in packages:
        try:
            if package == "scikit-learn":
                import sklearn
                dependencies[package] = sklearn.__version__
            elif package == "psycopg2-binary":
                import psycopg2
                dependencies[package] = psycopg2.__version__
            else:
                module = __import__(package)
                dependencies[package] = getattr(module, "__version__", "unknown")
        except ImportError:
            dependencies[package] = "not_installed"

    return dependencies