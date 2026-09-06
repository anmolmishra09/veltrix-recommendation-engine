"""
Redis connection and utilities.
"""
import redis
from .config import settings
import logging
import json
from typing import Any, Optional, Union
import pickle

logger = logging.getLogger(__name__)

# Create Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)

def get_redis():
    """
    Dependency to get a Redis client.
    """
    return redis_client

def set_cache(key: str, value: Any, expire: int = 3600, serialize: str = 'json'):
    """
    Set a value in the Redis cache.

    Args:
        key: Cache key.
        value: Value to cache.
        expire: Expiration time in seconds.
        serialize: Serialization method ('json' or 'pickle').
    """
    try:
        if serialize == 'json':
            serialized_value = json.dumps(value)
        elif serialize == 'pickle':
            serialized_value = pickle.dumps(value)
        else:
            raise ValueError(f"Unsupported serialization method: {serialize}")

        redis_client.setex(key, expire, serialized_value)
        logger.debug(f"Cached key '{key}' with expiration {expire}s")
    except Exception as e:
        logger.error(f"Failed to set cache key '{key}': {e}")

def get_cache(key: str, serialize: str = 'json') -> Any:
    """
    Get a value from the Redis cache.

    Args:
        key: Cache key.
        serialize: Serialization method ('json' or 'pickle').

    Returns:
        The cached value, or None if not found or expired.
    """
    try:
        serialized_value = redis_client.get(key)
        if serialized_value is None:
            return None

        if serialize == 'json':
            return json.loads(serialized_value)
        elif serialize == 'pickle':
            return pickle.loads(serialized_value)
        else:
            raise ValueError(f"Unsupported serialization method: {serialize}")
    except Exception as e:
        logger.error(f"Failed to get cache key '{key}': {e}")
        return None

def delete_cache(key: str):
    """
    Delete a value from the Redis cache.

    Args:
        key: Cache key.
    """
    try:
        redis_client.delete(key)
        logger.debug(f"Deleted cache key '{key}'")
    except Exception as e:
        logger.error(f"Failed to delete cache key '{key}': {e}")