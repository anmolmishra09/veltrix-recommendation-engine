"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from ..core.database import SessionLocal
from ..core.redis import get_redis
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
def health_check():
    """
    Basic health check.
    """
    return {"status": "healthy"}

@router.get("/ready")
def readiness_check(db: Session = Depends(SessionLocal), redis_client = Depends(get_redis)):
    """
    Readiness check: verify database and Redis connections.
    """
    try:
        # Check database
        db.execute("SELECT 1")
        # Check Redis
        redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "detail": str(e)}