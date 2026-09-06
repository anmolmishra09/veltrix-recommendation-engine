"""
User repository for database operations related to users.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
from ..core import models
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[models.User]:
        """
        Get user by ID.
        """
        return self.db.query(models.User).filter(models.User.id == user_id).first()

    def get_user_by_external_id(self, external_id: str) -> Optional[models.User]:
        """
        Get user by external ID (if applicable).
        In this model, we use the primary key as external ID.
        """
        if external_id.isdigit():
            return self.get_user(int(external_id))
        return None

    def get_users_by_ids(self, user_ids: List[int]) -> List[models.User]:
        """
        Get multiple users by their IDs.
        """
        if not user_ids:
            return []
        return self.db.query(models.User).filter(models.User.id.in_(user_ids)).all()

    def get_users_by_location(self, location: str, limit: int = 100) -> List[models.User]:
        """
        Get users by location.
        """
        return self.db.query(models.User).filter(
            models.User.location == location
        ).limit(limit).all()

    def search_users(self, query: str, limit: int = 50) -> List[models.User]:
        """
        Search users by location or metadata.
        """
        search_term = f"%{query}%"
        return self.db.query(models.User).filter(
            or_(
                models.User.location.ilike(search_term),
                models.User.metadata_.ilike(search_term) if models.User.metadata_ is not None else False
            )
        ).limit(limit).all()

    def get_active_users_since(self, since_date, limit: int = 1000) -> List[models.User]:
        """
        Get users who have been active since a given date.
        """
        from ..core import models  # Avoid circular import
        return self.db.query(models.User).join(
            models.Interaction, models.User.id == models.Interaction.user_id
        ).filter(
            models.Interaction.timestamp >= since_date
        ).distinct().limit(limit).all()

    def create_user(self, user: models.User) -> models.User:
        """
        Create a new user.
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Created user ID {user.id}")
        return user

    def update_user(self, user_id: int, updates: dict) -> Optional[models.User]:
        """
        Update a user.
        """
        user = self.get_user(user_id)
        if not user:
            return None
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Updated user ID {user.id}")
        return user

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        """
        user = self.get_user(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        logger.info(f"Deleted user ID {user_id}")
        return True