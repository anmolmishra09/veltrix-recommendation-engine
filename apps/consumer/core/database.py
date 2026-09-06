"""
Database connection and session management for consumer.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from ..core.config import consumer_settings

# Import models to ensure they are registered with Base
# Note: In a real implementation, you would import the actual models
# For now, we'll create a basic base

logger = logging.getLogger(__name__)

# Create database engine
if consumer_settings.DATABASE_URL:
    engine = create_engine(
        consumer_settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
else:
    # Fallback to SQLite for development
    engine = create_engine(
        "sqlite:///./consumer.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """
    Create all database tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise