"""
Centralized application configuration using Pydantic Settings.
"""
import os
from typing import List, Optional, Union
from pydantic import BaseSettings, Field, validator
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/recommendation_db",
        env="DATABASE_URL"
    )
    POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    ECHO: bool = Field(default=False, env="DATABASE_ECHO")


class RedisSettings(BaseSettings):
    """Redis configuration."""
    URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    DB: int = Field(default=0, env="REDIS_DB")
    PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")


class KafkaSettings(BaseSettings):
    """Kafka configuration."""
    BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    SECURITY_PROTOCOL: str = Field(
        default="PLAINTEXT",
        env="KAFKA_SECURITY_PROTOCOL"
    )
    SASL_MECHANISM: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_MECHANISM"
    )
    SASL_USERNAME: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_USERNAME"
    )
    SASL_PASSWORD: Optional[str] = Field(
        default=None,
        env="KAFKA_SASL_PASSWORD"
    )
    GROUP_ID: str = Field(
        default="recommendation-platform",
        env="KAFKA_GROUP_ID"
    )
    AUTO_OFFSET_RESET: str = Field(
        default="earliest",
        env="KAFKA_AUTO_OFFSET_RESET"
    )


class MLflowSettings(BaseSettings):
    """MLflow configuration."""
    TRACKING_URI: str = Field(
        default="http://localhost:5000",
        env="MLFLOW_TRACKING_URI"
    )
    ARTIFACT_ROOT: str = Field(
        default="./mlruns",
        env="MLFLOW_ARTIFACT_ROOT"
    )
    EXPERIMENT_NAME: str = Field(
        default="recommendation-platform",
        env="MLFLOW_EXPERIMENT_NAME"
    )


class FeatureStoreSettings(BaseSettings):
    """Feature store configuration."""
    REPO_PATH: str = Field(
        default="./feast_repository",
        env="FEAST_REPO_PATH"
    )
    TENANT: str = Field(
        default="recommendation-platform",
        env="FEAST_TENANT"
    )


class S3Settings(BaseSettings):
    """S3/MinIO configuration."""
    ENDPOINT: str = Field(
        default="http://localhost:9000",
        env="S3_ENDPOINT"
    )
    ACCESS_KEY: str = Field(
        default="minio",
        env="S3_ACCESS_KEY"
    )
    SECRET_KEY: str = Field(
        default="minio123",
        env="S3_SECRET_KEY"
    )
    BUCKET: str = Field(
        default="mlflow",
        env="S3_BUCKET"
    )
    SECURE: bool = Field(default=False, env="S3_SECURE")


class MonitoringSettings(BaseSettings):
    """Monitoring configuration."""
    ENABLE_TELEMETRY: bool = Field(
        default=True,
        env="ENABLE_TELEMETRY"
    )
    PROMETHEUS_PORT: int = Field(
        default=9090,
        env="PROMETHEUS_PORT"
    )
    METRICS_NAMESPACE: str = Field(
        default="recommendation_platform",
        env="METRICS_NAMESPACE"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    TRACING_ENDPOINT: Optional[str] = Field(
        default=None,
        env="TRACING_ENDPOINT"
    )


class APISettings(BaseSettings):
    """API configuration."""
    HOST: str = Field(default="0.0.0.0", env="API_HOST")
    PORT: int = Field(default=8000, env="API_PORT")
    DEBUG: bool = Field(default=False, env="API_DEBUG")
    WORKERS: int = Field(default=1, env="API_WORKERS")
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="API_CORS_ORIGINS"
    )
    TITLE: str = Field(
        default="Recommendation API",
        env="API_TITLE"
    )
    DESCRIPTION: str = Field(
        default="API for the recommendation platform",
        env="API_DESCRIPTION"
    )
    VERSION: str = Field(
        default="0.1.0",
        env="API_VERSION"
    )


class ModelSettings(BaseSettings):
    """ML model configuration."""
    EMBEDDING_DIM: int = Field(
        default=64,
        env="MODEL_EMBEDDING_DIM"
    )
    BATCH_SIZE: int = Field(
        default=256,
        env="MODEL_BATCH_SIZE"
    )
    LEARNING_RATE: float = Field(
        default=0.001,
        env="MODEL_LEARNING_RATE"
    )
    EPOCHS: int = Field(
        default=10,
        env="MODEL_EPOCHS"
    )
    VALIDATION_SPLIT: float = Field(
        default=0.2,
        env="MODEL_VALIDATION_SPLIT"
    )
    SEED: int = Field(
        default=42,
        env="MODEL_SEED"
    )


class RecommendationSettings(BaseSettings):
    """Recommendation engine configuration."""
    DEFAULT_K: int = Field(
        default=10,
        env="REC_DEFAULT_K"
    )
    MAX_K: int = Field(
        default=100,
        env="REC_MAX_K"
    )
    CANDIDATE_LIMIT_PER_SOURCE: int = Field(
        default=1000,
        env="REC_CANDIDATE_LIMIT_PER_SOURCE"
    )
    HYBRID_WEIGHTS: Dict[str, float] = Field(
        default={
            "collaborative": 0.35,
            "content": 0.25,
            "popularity": 0.15,
            "embedding": 0.25
        },
        env="REC_HYBRID_WEIGHTS"
    )
    RANKING_MODEL_TYPE: str = Field(
        default="xgboost",
        env="REC_RANKING_MODEL_TYPE"
    )
    COLD_START_ENABLED: bool = Field(
        default=True,
        env="REC_COLD_START_ENABLED"
    )


class Settings(BaseSettings):
    """Main application settings."""
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        env="ENVIRONMENT"
    )
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    kafka: KafkaSettings = KafkaSettings()
    mlflow: MLflowSettings = MLflowSettings()
    feature_store: FeatureStoreSettings = FeatureStoreSettings()
    s3: S3Settings = S3Settings()
    monitoring: MonitoringSettings = MonitoringSettings()
    api: APISettings = APISettings()
    model: ModelSettings = ModelSettings()
    recommendation: RecommendationSettings = RecommendationSettings()

    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()