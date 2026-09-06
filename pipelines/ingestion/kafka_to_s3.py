
"""
Script to consume events from Kafka and store them in S3-compatible storage (or local filesystem).
In a real implementation, this would use the confluent-kafka library to consume from Kafka
and write to S3/MinIO. For this example, we'll simulate the consumption by reading from
a file or generating sample data.
"""
import os
import json
import logging
from datetime import datetime
import pandas as pd

try:
    import numpy as np
except ImportError:
    # Create a simple mock for numpy.random if numpy is not available
    class MockNumpyRandom:
        def choice(self, lst):
            import random
            return random.choice(lst)

        def randint(self, low, high=None):
            import random
            if high is None:
                return random.randint(0, low)
            else:
                return random.randint(low, high)

    np = type('numpy', (), {'random': MockNumpyRandom()})()

logger = logging.getLogger(__name__)

def consume_and_store(kafka_topic: str = "user-events",
                      output_path: str = "./data/raw",
                      file_format: str = "json",
                      max_messages: int = 10000):
    """
    Consume events from Kafka and store them in the specified format.

    Args:
        kafka_topic: Kafka topic to consume from.
        output_path: Directory to store the consumed events.
        file_format: Format to store the data ('json', 'csv', 'parquet').
        max_messages: Maximum number of messages to consume.
    """
    logger.info(f"Starting consumption from Kafka topic {kafka_topic}")

    # In a real implementation, we would use:
    try:
        from confluent_kafka import Consumer, KafkaError
        KAFKA_AVAILABLE = True
    except ImportError:
        KAFKA_AVAILABLE = False
        logger.warning("Kafka dependencies not available. Will simulate consumption.")

    if KAFKA_AVAILABLE:
        # Real Kafka consumption
        conf = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'recommendation-platform-consumer',
            'auto.offset.reset': 'earliest'
        }

        consumer = Consumer(conf)
        consumer.subscribe([kafka_topic])

        events = []
        messages_consumed = 0

        try:
            while messages_consumed < max_messages:
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
                    events.append(event_data)
                    messages_consumed += 1

                    if messages_consumed % 100 == 0:
                        logger.info(f"Consumed {messages_consumed} messages")
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            consumer.close()
    else:
        # Simulate consumption (original behavior)
        logger.info("Using simulated Kafka consumption")

        # Check if we have a sample data file to simulate Kafka consumption
        sample_file = "./data/raw/sample_events.json"
        if os.path.exists(sample_file):
            logger.info(f"Reading sample events from {sample_file}")
            with open(sample_file, 'r') as f:
                events = [json.loads(line) for line in f]
        else:
            logger.info("Generating sample events")
            # Generate sample events
            events = []
            user_ids = [f'user_{i}' for i in range(1, 101)]
            product_ids = [f'product_{i}' for i in range(1, 51)]
            event_types = ['view', 'click', 'purchase', 'add_to_cart', 'like', 'wishlist', 'search', 'impression']

            for i in range(min(max_messages, 1000)):  # Generate up to 1000 sample events
                event = {
                    'user_id': np.random.choice(user_ids),
                    'product_id': np.random.choice(product_ids),
                    'event_type': np.random.choice(event_types),
                    'timestamp': int(datetime.now().timestamp()) - np.random.randint(0, 86400*7),  # Last 7 days
                    'session_id': f'session_{np.random.randint(1, 100)}',
                    'context': json.dumps({'source': np.random.choice(['homepage', 'search', 'email'])}),
                    'metadata': json.dumps({})
                }
                events.append(event)

    # Limit to max_messages
    events = events[:max_messages]

    # Convert to DataFrame
    df = pd.DataFrame(events)

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file_format == 'json':
        output_file = os.path.join(output_path, f"events_{timestamp}.json")
        df.to_json(output_file, orient='records', lines=True)
    elif file_format == 'csv':
        output_file = os.path.join(output_path, f"events_{timestamp}.csv")
        df.to_csv(output_file, index=False)
    elif file_format == 'parquet':
        output_file = os.path.join(output_path, f"events_{timestamp}.parquet")
        df.to_parquet(output_file, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    logger.info(f"Stored {len(events)} events to {output_file}")

    return output_file

def main():
    """
    Main function to run the Kafka consumer.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get configuration from environment or use defaults
    kafka_topic = os.getenv('KAFKA_TOPIC', 'user-events')
    output_path = os.getenv('OUTPUT_PATH', './data/raw')
    file_format = os.getenv('FILE_FORMAT', 'json')
    max_messages = int(os.getenv('MAX_MESSAGES', '10000'))

    logger.info(f"Consuming from topic: {kafka_topic}")
    logger.info(f"Storing to: {output_path}")
    logger.info(f"Format: {file_format}")
    logger.info(f"Max messages: {max_messages}")

    # Consume and store
    output_file = consume_and_store(
        kafka_topic=kafka_topic,
        output_path=output_path,
        file_format=file_format,
        max_messages=max_messages
    )

    logger.info(f"Successfully stored events to {output_file}")

if __name__ == "__main__":
    main()