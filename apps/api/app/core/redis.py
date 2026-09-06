"""
Redis connection helper.
"""
import redis
from ..core.config import settings

_redis_client = None

def get_redis():
    """
    Get a Redis client instance (singleton).
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=settings.redis_decode_responses,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30
        )
        # Test connection
        try:
            _redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Could not connect to Redis: {e}")
    return _redis_client