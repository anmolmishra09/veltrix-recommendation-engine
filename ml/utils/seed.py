"""
Utilities for setting random seeds to ensure reproducibility.
"""
import os
import random
import numpy as np
import torch
import tensorflow as tf
from typing import Optional, Dict, Any


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across different libraries.

    Args:
        seed: Random seed value
    """
    # Set Python built-in random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch random seed
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # for multi-GPU

    # Set TensorFlow random seed
    tf.random.set_seed(seed)

    # Set environment variable for hash-based operations
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Ensure deterministic behavior in PyTorch
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # Ensure deterministic behavior in TensorFlow
    os.environ['TF_DETERMINISTIC_OPS'] = '1'

    print(f"Random seeds set to {seed} for reproducibility")


def get_seed() -> int:
    """
    Get the current seed from environment or return default.

    Returns:
        Current seed value
    """
    return int(os.environ.get('PYTHONHASHSEED', 42))


def seed_worker(worker_id: int) -> None:
    """
    Set worker seed for DataLoader workers.

    Args:
        worker_id: Worker ID
    """
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)