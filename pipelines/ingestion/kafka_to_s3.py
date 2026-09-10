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
import boto3
from botocore.exceptions import ClientError

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

def get_s3_client():
    """
    Create and return an S3 client configured for MinIO/S3.
    """
    endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
    access_key = os.getenv('S3_ACCESS_KEY', 'minio')
    secret_key = os.getenv('S3_SECRET_KEY', 'minio123')

    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

def ensure_bucket_exists(s3_client, bucket_name):
    """
    Ensure that the S3 bucket exists, create it if it doesn't.
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} already exists")
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            logger.info(f"Bucket {bucket_name} does not exist. Creating...")
            s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} created")
        else:
            logger.error(f"Error checking bucket {bucket_name}: {e}")
            raise

def consume_and_store(kafka_topic: str = "user-events",
                      output_path: str = "./data/raw",
                      file_format: str = "json",
                      max_messages: int = 10000,
                      use_s3: bool = False,
                      s3_bucket: str = "ml-recommendation-raw"):
    """
    Consume events from Kafka and store them in the specified format.

    Args:
        kafka_topic: Kafka topic to consume from.
        output_path: Directory to store the consumed events (local) or S3 prefix.
        file_format: Format to store the data ('json', 'csv', 'parquet').
        max_messages: Maximum number of messages to consume.
        use_s3: Whether to store data in S3/MinIO instead of local filesystem.
        s3_bucket: S3 bucket name to use when use_s3=True.
    """
    logger.info(f"Starting consumption from Kafka topic {kafka_topic}")
    logger.info(f"Use S3 storage: {use_s3}")

    events = []

    # Try to use real Kafka consumption
    try:
        from confluent_kafka import Consumer, KafkaError
        KAFKA_AVAILABLE = True
        logger.info("Kafka library is available")
    except ImportError:
        KAFKA_AVAILABLE = False
        logger.warning("Kafka dependencies not available. Will simulate consumption.")

    if KAFKA_AVAILABLE:
        # Attempt real Kafka consumption with better error handling
        logger.info("Attempting to connect to Kafka...")
        conf = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'recommendation-platform-consumer',
            'auto.offset.reset': 'earliest',
            'session.timeout.ms': 6000,
            'max.poll.interval.ms': 300000
        }

        try:
            consumer = Consumer(conf)
            consumer.subscribe([kafka_topic])
            logger.info("Successfully created Kafka consumer")

            messages_consumed = 0
            consecutive_errors = 0
            max_consecutive_errors = 5

            try:
                while messages_consumed < max_messages:
                    try:
                        msg = consumer.poll(1.0)
                        if msg is None:
                            continue
                        if msg.error():
                            if msg.error().code() == KafkaError._PARTITION_EOF:
                                continue
                            else:
                                logger.error(f"Consumer error: {msg.error()}")
                                consecutive_errors += 1
                                if consecutive_errors >= max_consecutive_errors:
                                    logger.error("Too many consecutive errors, falling back to simulation")
                                    break
                                continue

                        # Process message
                        try:
                            event_data = json.loads(msg.value().decode('utf-8'))
                            events.append(event_data)
                            messages_consumed += 1
                            consecutive_errors = 0  # Reset error counter on success

                            if messages_consumed % 100 == 0:
                                logger.info(f"Consumed {messages_consumed} messages")
                        except Exception as e:
                            logger.error(f"Failed to process message: {e}")
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                logger.error("Too many consecutive errors, falling back to simulation")
                                break

                    except Exception as e:
                        logger.error(f"Error during poll operation: {e}")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error("Too many consecutive errors, falling back to simulation")
                            break

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
            finally:
                consumer.close()

            logger.info(f"Finished consuming from Kafka. Total messages: {len(events)}")

            # If we didn't get any messages, fall back to simulation
            if len(events) == 0:
                logger.warning("No messages consumed from Kafka, falling back to simulation")
                events = []

        except Exception as e:
            logger.warning(f"Failed to connect to or consume from Kafka: {e}")
            logger.info("Falling back to simulated consumption")
            events = []  # Reset events and fall back to simulation
    else:
        logger.info("Kafka library not available, using simulated consumption")

    # If we didn't get events from Kafka (either not available or connection failed), simulate
    if not events:
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

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if use_s3:
        # Store in S3/MinIO
        s3_client = get_s3_client()
        ensure_bucket_exists(s3_client, s3_bucket)

        # Convert DataFrame to the desired format in memory
        if file_format == 'json':
            # For JSON, we'll write each record as a line (JSON Lines format)
            csv_buffer = df.to_json(orient='records', lines=True)
            content_type = 'application/json'
        elif file_format == 'csv':
            csv_buffer = df.to_csv(index=False)
            content_type = 'text/csv'
        elif file_format == 'parquet':
            # For Parquet, we need to use bytes buffer
            from io import BytesIO
            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            csv_buffer = parquet_buffer.getvalue()
            content_type = 'application/octet-stream'
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        # Construct S3 key (path)
        s3_key = f"{output_path.rstrip('/')}/events_{timestamp}.{file_format}"

        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=csv_buffer,
                ContentType=content_type
            )
            logger.info(f"Stored {len(events)} events to s3://{s3_bucket}/{s3_key}")
            return f"s3://{s3_bucket}/{s3_key}"
        except Exception as e:
            logger.error(f"Failed to store data to S3: {e}")
            raise
    else:
        # Store locally (original behavior)
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

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
    use_s3 = os.getenv('USE_S3', 'false').lower() == 'true'
    s3_bucket = os.getenv('S3_BUCKET', 'ml-recommendation-raw')

    logger.info(f"Consuming from topic: {kafka_topic}")
    logger.info(f"Storing to: {'S3' if use_s3 else 'local filesystem'}")
    if use_s3:
        logger.info(f"S3 bucket: {s3_bucket}")
        logger.info(f"S3 prefix: {output_path}")
    else:
        logger.info(f"Local path: {output_path}")
    logger.info(f"Format: {file_format}")
    logger.info(f"Max messages: {max_messages}")

    # Consume and store
    output_location = consume_and_store(
        kafka_topic=kafka_topic,
        output_path=output_path,
        file_format=file_format,
        max_messages=max_messages,
        use_s3=use_s3,
        s3_bucket=s3_bucket
    )

    logger.info(f"Successfully stored events to {output_location}")

if __name__ == "__main__":
    main()