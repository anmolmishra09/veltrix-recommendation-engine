"""
Recommendation repository for database operations related to recommendations.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from ..core import models
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendation(self, recommendation_id: int) -> Optional[models.Recommendation]:
        """
        Get recommendation by ID.
        """
        return self.db.query(models.Recommendation).filter(models.Recommendation.id == recommendation_id).first()

    def get_user_recommendations(self, user_id: int, limit: int = 100) -> List[models.Recommendation]:
        """
        Get recommendations for a specific user.
        """
        return self.db.query(models.Recommendation).filter(
            models.Recommendation.user_id == user_id
        ).order_by(models.Recommendation.created_at.desc()).limit(limit).all()

    def get_recommendations_by_experiment(self, experiment_id: str, limit: int = 1000) -> List[models.Recommendation]:
        """
        Get recommendations for a specific experiment.
        """
        return self.db.query(models.Recommendation).filter(
            models.Recommendation.experiment_id == experiment_id
        ).order_by(models.Recommendation.created_at.desc()).limit(limit).all()

    def create_recommendation(self, recommendation: models.Recommendation) -> models.Recommendation:
        """
        Create a new recommendation record.
        """
        self.db.add(recommendation)
        self.db.commit()
        self.db.refresh(recommendation)
        logger.info(f"Created recommendation: user_id={recommendation.user_id}, experiment_id={recommendation.experiment_id}")
        return recommendation

    def update_recommendation(self, recommendation_id: int, recommendation_update: dict) -> Optional[models.Recommendation]:
        """
        Update an existing recommendation.
        """
        recommendation = self.get_recommendation(recommendation_id)
        if recommendation:
            for key, value in recommendation_update.items():
                setattr(recommendation, key, value)
            self.db.commit()
            self.db.refresh(recommendation)
            logger.info(f"Updated recommendation: {recommendation_id}")
        return recommendation

    def delete_recommendation(self, recommendation_id: int) -> bool:
        """
        Delete a recommendation.
        """
        recommendation = self.get_recommendation(recommendation_id)
        if recommendation:
            self.db.delete(recommendation)
            self.db.commit()
            logger.info(f"Deleted recommendation: {recommendation_id}")
            return True
        return False

    def get_recommendation_stats(self, experiment_id: Optional[str] = None) -> dict:
        """
        Get statistics about recommendations.
        """
        query = self.db.query(models.Recommendation)
        if experiment_id:
            query = query.filter(models.Recommendation.experiment_id == experiment_id)

        total_count = query.count()

        # Get experiment breakdown
        experiment_breakdown = self.db.query(
            models.Recommendation.experiment_id,
            models.Recommendation.model_version,
            func.count(models.Recommendation.id).label('count')
        ).group_by(
            models.Recommendation.experiment_id,
            models.Recommendation.model_version
        ).all()

        breakdown = {}
        for exp_id, model_ver, count in experiment_breakdown:
            if exp_id not in breakdown:
                breakdown[exp_id] = {}
            breakdown[exp_id][model_ver or "none"] = count

        return {
            "total_recommendations": total_count,
            "experiment_breakdown": breakdown
        }