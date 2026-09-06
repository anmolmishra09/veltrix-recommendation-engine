"""
Users endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
import logging

from ..core.database import SessionLocal, get_db
from sqlalchemy.orm import Session
from ..core.exceptions import UserNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter()

class UserResponse(BaseModel):
    id: Any
    external_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    registration_timestamp: Any
    metadata: Optional[Dict[str, Any]] = None

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: Any,
    db: Session = Depends(get_db)
):
    """
    Get a user by ID.
    """
    # TODO: Implement actual database query
    # For now, we'll return a mock user
    logger.info(f"Fetching user {user_id}")
    # Mock user
    return UserResponse(
        id=user_id,
        external_id=f"user_{user_id}",
        age=25,
        gender="male",
        location="New York",
        registration_timestamp="2026-01-01T00:00:00Z",
        metadata={"interests": ["electronics"]}
    )

@router.get("/")
def get_users(limit: int = 100):
    """
    Get a list of users (for debugging).
    """
    # TODO: Implement actual database query
    return [{"id": i, "external_id": f"user_{i}"} for i in range(1, limit+1)]