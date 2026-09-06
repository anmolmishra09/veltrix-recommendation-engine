"""
Event service for publishing events to Kafka and other sinks.
"""
import json
import logging
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self.logger = logger
        # In a real implementation, initialize Kafka producer here
        # self.producer = KafkaProducer(...)
        self._kafka_enabled = False
        if settings.kafka_bootstrap_servers:
            try:
                # Attempt to import and initialize Kafka producer
                from confluent_kafka import Producer
                self.producer = Producer({
                    'bootstrap.servers': settings.kafka_bootstrap_servers,
                    'client.id': 'recommendation-platform'
                })
                self._kafka_enabled = True
                self.logger.info("Kafka producer initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize Kafka producer: {e}")
                self._kafka_enabled = False
        else:
            self.logger.info("Kafka not configured; events will be logged only")

    def publish_event(self, topic: str, event: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Publish an event to a Kafka topic.
        """
        event_json = json.dumps(event)
        if self._kafka_enabled:
            try:
                self.producer.produce(
                    topic=topic,
                    value=event_json,
                    key=key,
                    callback=self._delivery_callback
                )
                self.producer.poll(0)  # Trigger delivery callbacks
                self.logger.debug(f"Published event to {topic}: {event_json[:200]}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to publish event to Kafka: {e}")
                return False
        else:
            # Fallback: log the event
            self.logger.info(f"EVENT (mock) -> {topic}: {event_json}")
            return True

    def _delivery_callback(self, err, msg):
        """
        Callback for Kafka message delivery.
        """
        if err is not None:
            self.logger.error(f"Message delivery failed: {err}")
        else:
            self.logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def flush(self):
        """
        Flush any pending messages.
        """
        if self._kafka_enabled:
            try:
                self.producer.flush()
            except Exception as e:
                self.logger.error(f"Error flushing Kafka producer: {e}")

    def close(self):
        """
        Close the producer.
        """
        if self._kafka_enabled:
            try:
                self.producer.flush()
            except Exception as e:
                self.logger.error(f"Error closing Kafka producer: {e}")