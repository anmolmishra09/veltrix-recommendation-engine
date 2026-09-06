"""
SQLAlchemy models for the recommendation platform.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Users table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True, index=True)
    registration_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    interactions = relationship("Interaction", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    experiment_assignments = relationship("ExperimentAssignment", back_populates="user")

# Products table
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    inventory = Column(Integer, default=0, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    interactions = relationship("Interaction", back_populates="product")

# Interactions table
class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    context_ = Column("context", JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    # For recommendation tracking
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True, index=True)
    ranking_position = Column(Integer, nullable=True)
    recommendation_score = Column(Float, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("event_type IN ('view', 'click', 'search', 'add_to_cart', 'purchase', 'like', 'wishlist', 'impression', 'experiment_exposure', 'experiment_outcome')", name="valid_event_type"),
        Index("idx_interactions_user_id", "user_id"),
        Index("idx_interactions_product_id", "product_id"),
        Index("idx_interactions_event_type", "event_type"),
        Index("idx_interactions_timestamp", "timestamp"),
        Index("idx_interactions_session_id", "session_id"),
        Index("idx_interactions_user_product", "user_id", "product_id"),
        Index("idx_interactions_user_event", "user_id", "event_type"),
        Index("idx_interactions_product_event", "product_id", "event_type"),
    )

    # Relationships
    user = relationship("User", back_populates="interactions")
    product = relationship("Product", back_populates="interactions")
    recommendation = relationship("Recommendation", back_populates="interactions")

# Recommendations table
class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    context_ = Column("context", JSON, nullable=True)
    model_version = Column(String(100), nullable=True, index=True)
    experiment_id = Column(String(100), nullable=True, index=True)
    num_candidates = Column(Integer, nullable=True)
    num_returned = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    interactions = relationship("Interaction", back_populates="recommendation")

    # Indexes
    __table_args__ = (
        Index("idx_recommendations_user_id", "user_id"),
        Index("idx_recommendations_created_at", "created_at"),
        Index("idx_recommendations_model_version", "model_version"),
        Index("idx_recommendations_experiment_id", "experiment_id"),
    )

# Experiments table
class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_timestamp = Column(DateTime, nullable=True, index=True)
    end_timestamp = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    config_ = Column("config", JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'completed', 'cancelled')", name="valid_experiment_status"),
        Index("idx_experiments_status", "status"),
        Index("idx_experiments_start", "start_timestamp"),
        Index("idx_experiments_end", "end_timestamp"),
    )

    # Relationships
    experiment_assignments = relationship("ExperimentAssignment", back_populates="experiment")

# Experiment assignments table
class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    variant = Column(String(50), nullable=False, index=True)
    model_version = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint("experiment_id", "user_id", name="unique_experiment_user"),
        Index("idx_experiment_assignments_experiment", "experiment_id"),
        Index("idx_experiment_assignments_user", "user_id"),
        Index("idx_experiment_assignments_variant", "variant"),
    )

    # Relationships
    experiment = relationship("Experiment", back_populates="experiment_assignments")
    user = relationship("User", back_populates="experiment_assignments")