"""
Application configuration.
"""
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Recommendation API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/recommendation_db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Feature Store
    FEAST_FEATURE_STORE_PATH: str = os.getenv("FEAST_FEATURE_STORE_PATH", "/feast/feast_repository")

    # MLflow
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    # Security (placeholder)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Monitoring
    ENABLE_TELEMETRY: bool = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"

    class Config:
        env_file = ".env"

settings = Settings()