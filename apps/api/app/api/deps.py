"""
API dependencies.
"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from ..core.database import get_db, SessionLocal
from ..core.redis import get_redis
from ..core.config import settings

def get_db() -> Generator:
    """
    Dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis_client():
    """
    Dependency to get a Redis client.
    """
    return get_redis()

# Additional dependencies can be added here (e.g., for ML models, feature store, etc.)