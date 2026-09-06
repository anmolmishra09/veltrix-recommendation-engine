"""
Experiment repository for database operations related to experiments.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from ..core import models
from ..core.exceptions import ExperimentNotFoundException
import logging

logger = logging.getLogger(__name__)

class ExperimentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_experiment_by_id(self, experiment_id: str) -> Optional[models.Experiment]:
        """
        Get experiment by experiment_id.
        """
        return self.db.query(models.Experiment).filter(models.Experiment.experiment_id == experiment_id).first()

    def get_experiment(self, experiment_id: int) -> Optional[models.Experiment]:
        """
        Get experiment by internal ID.
        """
        return self.db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()

    def get_experiments(self, status: Optional[str] = None, limit: int = 100) -> List[models.Experiment]:
        """
        Get list of experiments, optionally filtered by status.
        """
        query = self.db.query(models.Experiment)
        if status:
            query = query.filter(models.Experiment.status == status)
        return query.limit(limit).all()

    def create_experiment(self, experiment: models.Experiment) -> models.Experiment:
        """
        Create a new experiment.
        """
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        logger.info(f"Created experiment: {experiment.experiment_id}")
        return experiment

    def update_experiment(self, experiment_id: int, experiment_update: dict) -> Optional[models.Experiment]:
        """
        Update an existing experiment.
        """
        experiment = self.get_experiment(experiment_id)
        if experiment:
            for key, value in experiment_update.items():
                setattr(experiment, key, value)
            self.db.commit()
            self.db.refresh(experiment)
            logger.info(f"Updated experiment: {experiment.experiment_id}")
        return experiment

    def delete_experiment(self, experiment_id: int) -> bool:
        """
        Delete an experiment.
        """
        experiment = self.get_experiment(experiment_id)
        if experiment:
            self.db.delete(experiment)
            self.db.commit()
            logger.info(f"Deleted experiment: {experiment.experiment_id}")
            return True
        return False

    # Experiment assignment methods
    def get_experiment_assignment(self, experiment_id: int, user_id: int) -> Optional[models.ExperimentAssignment]:
        """
        Get experiment assignment for a specific user and experiment.
        """
        return self.db.query(models.ExperimentAssignment).filter(
            models.ExperimentAssignment.experiment_id == experiment_id,
            models.ExperimentAssignment.user_id == user_id
        ).first()

    def get_user_experiment_assignments(self, user_id: int) -> List[models.ExperimentAssignment]:
        """
        Get all experiment assignments for a user.
        """
        return self.db.query(models.ExperimentAssignment).filter(
            models.ExperimentAssignment.user_id == user_id
        ).all()

    def get_experiment_assignments(self, experiment_id: int) -> List[models.ExperimentAssignment]:
        """
        Get all assignments for a specific experiment.
        """
        return self.db.query(models.ExperimentAssignment).filter(
            models.ExperimentAssignment.experiment_id == experiment_id
        ).all()

    def create_experiment_assignment(self, assignment: models.ExperimentAssignment) -> models.ExperimentAssignment:
        """
        Create a new experiment assignment.
        """
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        logger.info(f"Created experiment assignment: experiment_id={assignment.experiment_id}, user_id={assignment.user_id}, variant={assignment.variant}")
        return assignment

    def update_experiment_assignment(self, assignment_id: int, assignment_update: dict) -> Optional[models.ExperimentAssignment]:
        """
        Update an existing experiment assignment.
        """
        assignment = self.db.query(models.ExperimentAssignment).filter(models.ExperimentAssignment.id == assignment_id).first()
        if assignment:
            for key, value in assignment_update.items():
                setattr(assignment, key, value)
            self.db.commit()
            self.db.refresh(assignment)
            logger.info(f"Updated experiment assignment: {assignment.id}")
        return assignment

    def delete_experiment_assignment(self, assignment_id: int) -> bool:
        """
        Delete an experiment assignment.
        """
        assignment = self.db.query(models.ExperimentAssignment).filter(models.ExperimentAssignment.id == assignment_id).first()
        if assignment:
            self.db.delete(assignment)
            self.db.commit()
            logger.info(f"Deleted experiment assignment: {assignment_id}")
            return True
        return False