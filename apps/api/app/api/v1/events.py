"""
Events endpoint for ingesting user interactions with Kafka integration.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Any, Optional, Dict
import logging
import time
import json
import uuid

# Try to import Kafka dependencies
try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka dependencies not available. Events will be logged only.")

from ..core.database import SessionLocal
from ..core.redis import get_redis
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class Event(BaseModel):
    user_id: Any = Field(..., description="The ID of the user")
    product_id: Any = Field(..., description="The ID of the product")
    event_type: str = Field(..., description="Type of event (view, click, purchase, etc.)")
    timestamp: Optional[Any] = Field(None, description="Timestamp of the event (if not provided, will be set to now)")
    session_id: Optional[str] = Field(None, description="Session ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")

class EventsResponse(BaseModel):
    status: str
    message: str
    event_id: Optional[Any] = None

# In-memory storage for events (for demonstration only)
# In a real app, we would send to Kafka and then store in a data lake
events_store = []

# Kafka producer (if available)
def get_kafka_producer():
    if not KAFKA_AVAILABLE:
        return None

    try:
        conf = {
            'bootstrap.servers': getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'client.id': 'recommendation-platform-producer'
        }
        return Producer(conf)
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        return None

@router.post("/", response_model=EventsResponse)
def ingest_event(
    event: Event,
    background_tasks: BackgroundTasks,
    db: Session = Depends(SessionLocal),
    redis_client = Depends(get_redis)
):
    """
    Ingest a user interaction event and send to Kafka.
    """
    # Set timestamp if not provided
    if event.timestamp is None:
        event.timestamp = int(time.time())

    # Generate unique event ID
    event_id = str(uuid.uuid4())

    # Prepare event for Kafka
    event_dict = {
        "event_id": event_id,
        "user_id": str(event.user_id),
        "product_id": str(event.product_id) if event.product_id is not None else None,
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "session_id": event.session_id,
        "context": event.context or {},
        "metadata": event.metadata or {}
    }

    # Store locally for debugging/demo purposes
    events_store.append(event_dict)

    # Send to Kafka if available
    if KAFKA_AVAILABLE:
        try:
            producer = get_kafka_producer()
            if producer:
                # Produce to user-events topic
                producer.produce(
                    topic='user-events',
                    key=str(event.user_id),
                    value=json.dumps(event_dict),
                    callback=lambda err, msg: logger.info(f"Event sent to Kafka: {err}") if err else None
                )
                producer.poll(0)  # Trigger delivery callbacks
                logger.info(f"Event queued for Kafka: {event_id}")
            else:
                logger.warning("Kafka producer not available, logging event only")
                logger.info(f"Ingested event: {event_dict}")
        except Exception as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            logger.info(f"Ingested event (Kafka failed): {event_dict}")
    else:
        # Fallback to logging only
        logger.info(f"Ingested event: {event_dict}")

    # Update feature store asynchronously (via background task that would consume from Kafka)
    # In a real implementation, this would trigger a feature update process
    background_tasks.add_task(update_feature_store, event_dict)

    response = EventsResponse(
        status="success",
        message="Event ingested successfully",
        event_id=event_id
    )

    return response

def update_feature_store(event_dict: dict):
    """
    Background task to update feature store based on events.
    In a real implementation, this would consume from Kafka and update features.
    """
    # This is a placeholder for the background task that would consume from Kafka
    # and update the feature store for model training
    logger.info(f"Would update feature store with event: {event_dict['event_id']}")
    # In reality, this would connect to Kafka consumer group and process events

@router.get("/")
def get_events(limit: int = 100):
    """
    Get recent events (for debugging).
    """
    return events_store[-limit:]

@router.get("/kafka/status")
def kafka_status():
    """
    Check Kafka connection status.
    """
    if not KAFKA_AVAILABLE:
        return {"status": "unavailable", "message": "Kafka dependencies not installed"}

    try:
        producer = get_kafka_producer()
        if producer:
            # Try to get metadata to test connection
            metadata = producer.list_topics(timeout=5)
            return {"status": "connected", "brokers": len(metadata.brokers)}
        else:
            return {"status": "disconnected", "message": "Failed to create producer"}
    except Exception as e:
        return {"status": "error", "message": str(e)}