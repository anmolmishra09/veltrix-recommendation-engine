"""
Consumer configuration.
"""
from pydantic import BaseSettings
from ..core.config import settings as base_settings


class ConsumerSettings(BaseSettings):
    """Consumer-specific configuration."""
    # Override port for consumer
    PORT: int = Field(default=8001, env="CONSUMER_PORT")

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="kafka:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )

    # Redis settings
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        env="REDIS_URL"
    )

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/recommendation_db",
        env="DATABASE_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global consumer settings instance
consumer_settings = ConsumerSettings()