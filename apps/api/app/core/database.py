"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from ..core.config import settings

# Import models to ensure they are registered with Base
from . import models

logger = logging.getLogger(__name__)

# Create database engine
if settings.database.URL:
    engine = create_engine(
        settings.database.URL,
        pool_pre_ping=True,
        pool_size=settings.database.POOL_SIZE,
        max_overflow=settings.database.MAX_OVERFLOW,
        echo=settings.database.ECHO
    )
else:
    # Fallback to SQLite for development
    engine = create_engine(
        "sqlite:///./recommendation_platform.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
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
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise