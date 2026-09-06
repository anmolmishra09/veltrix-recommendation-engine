"""
Consumer application for processing events from Kafka.
"""
import asyncio
import json
import logging
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Try to import Kafka dependencies
try:
    from confluent_kafka import Consumer, KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka dependencies not available. Consumer will run without Kafka.")

from .core.config import consumer_settings
from .core.database import SessionLocal, create_tables, get_db
from .core import models

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Recommendation Platform Consumer",
    description="Consumer service for processing events from Kafka",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to the Recommendation Platform Consumer",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """
    Basic health check.
    """
    return {"status": "healthy"}

# Background task to consume events from Kafka
async def consume_events():
    """Consume events from Kafka and process them."""
    if not KAFKA_AVAILABLE:
        logger.warning("Kafka not available, skipping event consumption")
        return

    try:
        conf = {
            'bootstrap.servers': consumer_settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'recommendation-platform-consumer',
            'auto.offset.reset': 'earliest'
        }

        consumer = Consumer(conf)
        consumer.subscribe(['user-events', 'product-events', 'purchase-events', 'recommendation-events'])

        logger.info("Started Kafka consumer")

        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    break

            # Process message
            try:
                event_data = json.loads(msg.value().decode('utf-8'))
                await process_event(event_data)
                logger.debug(f"Processed event: {event_data.get('event_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize Kafka consumer: {e}")
    finally:
        consumer.close()


async def process_event(event_data: Dict[str, Any]) -> None:
    """
    Process a single event.
    In a real implementation, this would update feature stores, trigger model retraining, etc.
    """
    logger.info(f"Processing event: {event_data.get('event_type', 'unknown')}")

    # Store event in database
    try:
        db = SessionLocal()
        processed_event = models.ProcessedEvent(
            event_id=event_data.get("event_id", ""),
            event_type=event_data.get("event_type", ""),
            user_id=str(event_data.get("user_id", "")) if event_data.get("user_id") else None,
            product_id=str(event_data.get("product_id", "")) if event_data.get("product_id") else None,
            payload=event_data
        )
        db.add(processed_event)
        db.commit()
        db.refresh(processed_event)
        db.close()
        logger.debug(f"Stored event {processed_event.event_id} in database")
    except Exception as e:
        logger.error(f"Failed to store event in database: {e}")
        if 'db' in locals():
            db.close()

    # Example: If it's a purchase event, we might want to update user/product features
    if event_data.get("event_type") == "purchase":
        logger.info(f"Purchase event: {event_data.get('user_id')} purchased {event_data.get('product_id')}")

    # Simulate some processing work
    await asyncio.sleep(0.01)


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """
    Initialize the consumer on startup.
    """
    logger.info("Starting up the recommendation platform consumer")
    create_tables()
    logger.info("Database tables created")

    # Start consuming events in the background
    asyncio.create_task(consume_events())
    logger.info("Started event consumption task")

    logger.info("Recommendation platform consumer startup complete")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)