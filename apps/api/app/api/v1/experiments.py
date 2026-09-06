"""
Experiments endpoint for A/B testing.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, Dict, List
import logging

from ..core.database import SessionLocal, get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

class ExperimentResponse(BaseModel):
    id: Any
    experiment_id: str
    name: str
    description: Optional[str] = None
    start_timestamp: Any
    end_timestamp: Optional[Any] = None
    status: str
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ExperimentAssignmentResponse(BaseModel):
    id: Any
    experiment_id: Any
    user_id: Any
    variant: str
    model_version: Optional[str] = None
    assigned_at: Any
    metadata: Optional[Dict[str, Any]] = None

@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: Any,
    db: Session = Depends(get_db)
):
    """
    Get an experiment by ID.
    """
    # TODO: Implement actual database query
    # For now, we'll return a mock experiment
    logger.info(f"Fetching experiment {experiment_id}")
    return ExperimentResponse(
        id=1,
        experiment_id=str(experiment_id),
        name=f"Experiment {experiment_id}",
        description="A sample experiment",
        start_timestamp="2026-09-01T00:00:00Z",
        end_timestamp="2026-09-30T23:59:59Z",
        status="active",
        config={"traffic_allocation": {"control": 0.5, "treatment": 0.5}},
        metadata={"owner": "ml-team"}
    )

@router.get("/{experiment_id}/assignments/{user_id}", response_model=ExperimentAssignmentResponse)
def get_user_experiment_assignment(
    experiment_id: Any,
    user_id: Any,
    db: Session = Depends(get_db)
):
    """
    Get a user's assignment in an experiment.
    """
    # TODO: Implement actual database query
    # For now, we'll return a mock assignment
    logger.info(f"Fetching assignment for user {user_id} in experiment {experiment_id}")
    return ExperimentAssignmentResponse(
        id=1,
        experiment_id=experiment_id,
        user_id=user_id,
        variant="control",
        model_version="v1.0.0",
        assigned_at="2026-09-01T00:00:00Z",
        metadata={}
    )

@router.get("/")
def get_experiments(limit: int = 100):
    """
    Get a list of experiments (for debugging).
    """
    # TODO: Implement actual database query
    return [{"id": i, "experiment_id": f"exp_{i}"} for i in range(1, limit+1)]