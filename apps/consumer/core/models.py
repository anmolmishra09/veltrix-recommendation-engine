"""
SQLAlchemy models for the consumer.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Create base class for declarative models
Base = declarative_base()

# We'll define basic models that the consumer might need
# In a real implementation, these would match the models in the main application

class ProcessedEvent(Base):
    """Model for tracking processed events."""
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    product_id = Column(String(255), nullable=True, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    payload = Column(JSON, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_processed_events_event_id", "event_id"),
        Index("idx_processed_events_event_type", "event_type"),
        Index("idx_processed_events_user_id", "user_id"),
        Index("idx_processed_events_product_id", "product_id"),
        Index("idx_processed_events_processed_at", "processed_at"),
    )