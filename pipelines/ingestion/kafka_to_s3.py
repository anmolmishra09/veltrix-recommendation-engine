
import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError, EndpointConnectionError


# ---------------------------------------------------------------------------
# Optional NumPy dependency
# ---------------------------------------------------------------------------

try:
    import numpy as np
except ImportError:
    np = None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S3 / MinIO Configuration
# ---------------------------------------------------------------------------

def get_s3_client():
    """
    Create an S3 client configured for AWS S3 or MinIO.
    """

    endpoint_url = os.getenv(
        "S3_ENDPOINT_URL",
        "http://localhost:9000"
    )

    access_key = os.getenv(
        "S3_ACCESS_KEY",
        "minio"
    )

    secret_key = os.getenv(
        "S3_SECRET_KEY",
        "minio123"
    )

    region = os.getenv(
        "AWS_REGION",
        "us-east-1"
    )

    logger.info("Creating S3 client")
    logger.info("S3 endpoint: %s", endpoint_url)

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def ensure_bucket_exists(
    s3_client,
    bucket_name: str
) -> None:
    """
    Check whether an S3/MinIO bucket exists.
    Create it if it does not exist.
    """

    try:
        s3_client.head_bucket(
            Bucket=bucket_name
        )

        logger.info(
            "Bucket '%s' already exists",
            bucket_name
        )

    except ClientError as exc:
        error_code = str(
            exc.response.get("Error", {}).get("Code", "")
        )

        if error_code in {"404", "NoSuchBucket", "NotFound"}:
            logger.info(
                "Bucket '%s' does not exist. Creating it...",
                bucket_name
            )

            try:
                s3_client.create_bucket(
                    Bucket=bucket_name
                )

                logger.info(
                    "Bucket '%s' created successfully",
                    bucket_name
                )

            except ClientError:
                logger.exception(
                    "Failed to create bucket '%s'",
                    bucket_name
                )
                raise

        else:
            logger.exception(
                "Unable to check bucket '%s'",
                bucket_name
            )
            raise


# ---------------------------------------------------------------------------
# Sample Event Generation
# ---------------------------------------------------------------------------

def generate_sample_events(
    count: int = 1000
) -> List[Dict[str, Any]]:
    """
    Generate sample recommendation-system events.
    """

    logger.info(
        "Generating %d simulated events",
        count
    )

    user_ids = [
        f"user_{i}"
        for i in range(1, 101)
    ]

    product_ids = [
        f"product_{i}"
        for i in range(1, 51)
    ]

    event_types = [
        "view",
        "click",
        "purchase",
        "add_to_cart",
        "like",
        "wishlist",
        "search",
        "impression",
    ]

    sources = [
        "homepage",
        "search",
        "email",
        "recommendation",
        "category",
    ]

    events = []

    for i in range(count):

        if np is not None:
            user_id = np.random.choice(user_ids)
            product_id = np.random.choice(product_ids)
            event_type = np.random.choice(event_types)
            source = np.random.choice(sources)
            days_ago_seconds = np.random.randint(
                0,
                86400 * 7
            )
            session_number = np.random.randint(
                1,
                100
            )
        else:
            import random

            user_id = random.choice(user_ids)
            product_id = random.choice(product_ids)
            event_type = random.choice(event_types)
            source = random.choice(sources)
            days_ago_seconds = random.randint(
                0,
                86400 * 7
            )
            session_number = random.randint(
                1,
                100
            )

        event = {
            "event_id": f"event_{i + 1}",
            "user_id": user_id,
            "product_id": product_id,
            "event_type": event_type,
            "timestamp": int(
                datetime.now().timestamp()
            ) - days_ago_seconds,
            "session_id": f"session_{session_number}",
            "context": {
                "source": source
            },
            "metadata": {},
        }

        events.append(event)

    return events


# ---------------------------------------------------------------------------
# Sample File Loading
# ---------------------------------------------------------------------------

def load_sample_events(
    sample_file: str,
    max_messages: int
) -> List[Dict[str, Any]]:
    """
    Load JSON Lines events from a sample file.
    """

    if not os.path.exists(sample_file):
        return []

    logger.info(
        "Loading sample events from %s",
        sample_file
    )

    events = []

    try:
        with open(
            sample_file,
            "r",
            encoding="utf-8"
        ) as file:

            for line_number, line in enumerate(file, start=1):

                if len(events) >= max_messages:
                    break

                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)

                    if isinstance(event, dict):
                        events.append(event)

                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Skipping invalid JSON at line %d: %s",
                        line_number,
                        exc
                    )

    except OSError:
        logger.exception(
            "Unable to read sample file: %s",
            sample_file
        )

    logger.info(
        "Loaded %d events from sample file",
        len(events)
    )

    return events


# ---------------------------------------------------------------------------
# Kafka Consumption
# ---------------------------------------------------------------------------

def consume_from_kafka(
    kafka_topic: str,
    max_messages: int
) -> List[Dict[str, Any]]:
    """
    Consume events from Kafka.

    Returns an empty list when Kafka is unavailable or no valid
    messages are consumed.
    """

    try:
        from confluent_kafka import (
            Consumer,
            KafkaError,
        )

    except ImportError:
        logger.warning(
            "confluent-kafka is not installed."
        )

        return []

    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )

    group_id = os.getenv(
        "KAFKA_GROUP_ID",
        "recommendation-platform-consumer"
    )

    logger.info(
        "Connecting to Kafka: %s",
        bootstrap_servers
    )

    configuration = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "session.timeout.ms": 6000,
        "max.poll.interval.ms": 300000,
    }

    consumer = None
    events: List[Dict[str, Any]] = []

    try:

        consumer = Consumer(configuration)

        consumer.subscribe([kafka_topic])

        logger.info(
            "Subscribed to Kafka topic '%s'",
            kafka_topic
        )

        consecutive_errors = 0
        max_consecutive_errors = 5

        while len(events) < max_messages:

            try:
                message = consumer.poll(
                    timeout=1.0
                )

                if message is None:
                    continue

                if message.error():

                    if (
                        message.error().code()
                        == KafkaError._PARTITION_EOF
                    ):
                        continue

                    logger.error(
                        "Kafka consumer error: %s",
                        message.error()
                    )

                    consecutive_errors += 1

                    if (
                        consecutive_errors
                        >= max_consecutive_errors
                    ):
                        logger.error(
                            "Too many Kafka errors."
                        )
                        break

                    continue

                raw_value = message.value()

                if raw_value is None:
                    logger.warning(
                        "Received empty Kafka message"
                    )
                    continue

                try:

                    decoded_value = raw_value.decode(
                        "utf-8"
                    )

                    event = json.loads(
                        decoded_value
                    )

                    if not isinstance(event, dict):
                        logger.warning(
                            "Kafka message is not a JSON object"
                        )
                        continue

                    events.append(event)

                    consecutive_errors = 0

                    if len(events) % 100 == 0:
                        logger.info(
                            "Consumed %d/%d messages",
                            len(events),
                            max_messages
                        )

                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError
                ) as exc:

                    logger.warning(
                        "Invalid Kafka message: %s",
                        exc
                    )

            except Exception as exc:

                logger.exception(
                    "Error while polling Kafka: %s",
                    exc
                )

                consecutive_errors += 1

                if (
                    consecutive_errors
                    >= max_consecutive_errors
                ):
                    break

    except Exception as exc:

        logger.exception(
            "Unable to connect to Kafka: %s",
            exc
        )

        return []

    finally:

        if consumer is not None:
            try:
                consumer.close()
                logger.info(
                    "Kafka consumer closed"
                )
            except Exception:
                logger.exception(
                    "Error while closing Kafka consumer"
                )

    logger.info(
        "Kafka consumption completed. Events: %d",
        len(events)
    )

    return events


# ---------------------------------------------------------------------------
# DataFrame Conversion
# ---------------------------------------------------------------------------

def events_to_dataframe(
    events: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Convert events to a Pandas DataFrame.
    """

    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)

    # Convert nested objects to JSON strings.
    for column in ["context", "metadata"]:

        if column in df.columns:

            df[column] = df[column].apply(
                lambda value: json.dumps(value)
                if isinstance(value, (dict, list))
                else value
            )

    return df


# ---------------------------------------------------------------------------
# Local Storage
# ---------------------------------------------------------------------------

def store_locally(
    df: pd.DataFrame,
    output_path: str,
    file_format: str,
    timestamp: str
) -> str:
    """
    Store DataFrame on the local filesystem.
    """

    os.makedirs(
        output_path,
        exist_ok=True
    )

    file_format = file_format.lower()

    output_file = os.path.join(
        output_path,
        f"events_{timestamp}.{file_format}"
    )

    if file_format == "json":

        df.to_json(
            output_file,
            orient="records",
            lines=True,
            force_ascii=False
        )

    elif file_format == "csv":

        df.to_csv(
            output_file,
            index=False
        )

    elif file_format == "parquet":

        try:
            df.to_parquet(
                output_file,
                index=False,
                engine="pyarrow"
            )

        except ImportError as exc:

            raise RuntimeError(
                "Parquet support requires pyarrow. "
                "Install it with: pip install pyarrow"
            ) from exc

    else:

        raise ValueError(
            f"Unsupported file format: {file_format}. "
            "Use json, csv, or parquet."
        )

    logger.info(
        "Stored %d events locally: %s",
        len(df),
        output_file
    )

    return output_file


# ---------------------------------------------------------------------------
# S3 / MinIO Storage
# ---------------------------------------------------------------------------

def store_to_s3(
    df: pd.DataFrame,
    output_path: str,
    file_format: str,
    timestamp: str,
    bucket_name: str
) -> str:
    """
    Store DataFrame in S3-compatible storage.
    """

    s3_client = get_s3_client()

    ensure_bucket_exists(
        s3_client,
        bucket_name
    )

    file_format = file_format.lower()

    if file_format == "json":

        body = df.to_json(
            orient="records",
            lines=True,
            force_ascii=False
        ).encode("utf-8")

        content_type = (
            "application/x-ndjson"
        )

    elif file_format == "csv":

        body = df.to_csv(
            index=False
        ).encode("utf-8")

        content_type = "text/csv"

    elif file_format == "parquet":

        parquet_buffer = io.BytesIO()

        try:

            df.to_parquet(
                parquet_buffer,
                index=False,
                engine="pyarrow"
            )

        except ImportError as exc:

            raise RuntimeError(
                "Parquet support requires pyarrow. "
                "Install it with: pip install pyarrow"
            ) from exc

        parquet_buffer.seek(0)

        body = parquet_buffer.getvalue()

        content_type = (
            "application/octet-stream"
        )

    else:

        raise ValueError(
            f"Unsupported file format: {file_format}. "
            "Use json, csv, or parquet."
        )

    prefix = output_path.strip("/")

    if prefix:
        s3_key = (
            f"{prefix}/"
            f"events_{timestamp}.{file_format}"
        )
    else:
        s3_key = (
            f"events_{timestamp}.{file_format}"
        )

    try:

        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=body,
            ContentType=content_type,
        )

    except (
        ClientError,
        EndpointConnectionError
    ):

        logger.exception(
            "Failed to upload data to S3/MinIO"
        )

        raise

    location = (
        f"s3://{bucket_name}/{s3_key}"
    )

    logger.info(
        "Stored %d events to %s",
        len(df),
        location
    )

    return location


# ---------------------------------------------------------------------------
# Main Consumer Function
# ---------------------------------------------------------------------------

def consume_and_store(
    kafka_topic: str = "user-events",
    output_path: str = "./data/raw",
    file_format: str = "json",
    max_messages: int = 10000,
    use_s3: bool = False,
    s3_bucket: str = "ml-recommendation-raw",
) -> str:
    """
    Consume Kafka events and store them locally or in S3/MinIO.
    """

    if max_messages <= 0:
        raise ValueError(
            "max_messages must be greater than 0"
        )

    file_format = file_format.lower()

    if file_format not in {
        "json",
        "csv",
        "parquet",
    }:
        raise ValueError(
            "file_format must be json, csv, or parquet"
        )

    logger.info(
        "Starting event consumption"
    )

    logger.info(
        "Kafka topic: %s",
        kafka_topic
    )

    logger.info(
        "Maximum messages: %d",
        max_messages
    )

    logger.info(
        "Storage: %s",
        "S3/MinIO" if use_s3 else "Local"
    )

    # ---------------------------------------------------------------
    # 1. Try Kafka
    # ---------------------------------------------------------------

    events = consume_from_kafka(
        kafka_topic=kafka_topic,
        max_messages=max_messages
    )

    # ---------------------------------------------------------------
    # 2. Fallback to sample_events.json
    # ---------------------------------------------------------------

    if not events:

        logger.warning(
            "No events received from Kafka."
        )

        sample_file = os.path.join(
            "./data/raw",
            "sample_events.json"
        )

        events = load_sample_events(
            sample_file,
            max_messages
        )

    # ---------------------------------------------------------------
    # 3. Fallback to generated data
    # ---------------------------------------------------------------

    if not events:

        logger.warning(
            "No sample events found."
        )

        logger.info(
            "Generating simulated events."
        )

        events = generate_sample_events(
            min(max_messages, 1000)
        )

    # ---------------------------------------------------------------
    # 4. Limit event count
    # ---------------------------------------------------------------

    events = events[:max_messages]

    if not events:
        raise RuntimeError(
            "No events available to store."
        )

    logger.info(
        "Total events to store: %d",
        len(events)
    )

    # ---------------------------------------------------------------
    # 5. DataFrame
    # ---------------------------------------------------------------

    df = events_to_dataframe(events)

    if df.empty:
        raise RuntimeError(
            "Generated event DataFrame is empty."
        )

    logger.info(
        "DataFrame shape: %s",
        df.shape
    )

    # ---------------------------------------------------------------
    # 6. Timestamp
    # ---------------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    # ---------------------------------------------------------------
    # 7. Store
    # ---------------------------------------------------------------

    if use_s3:

        return store_to_s3(
            df=df,
            output_path=output_path,
            file_format=file_format,
            timestamp=timestamp,
            bucket_name=s3_bucket
        )

    return store_locally(
        df=df,
        output_path=output_path,
        file_format=file_format,
        timestamp=timestamp
    )


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Application entry point.
    """

    logging.basicConfig(
        level=os.getenv(
            "LOG_LEVEL",
            "INFO"
        ).upper(),
        format=(
            "%(asctime)s - "
            "%(name)s - "
            "%(levelname)s - "
            "%(message)s"
        )
    )

    kafka_topic = os.getenv(
        "KAFKA_TOPIC",
        "user-events"
    )

    output_path = os.getenv(
        "OUTPUT_PATH",
        "./data/raw"
    )

    file_format = os.getenv(
        "FILE_FORMAT",
        "json"
    )

    try:

        max_messages = int(
            os.getenv(
                "MAX_MESSAGES",
                "10000"
            )
        )

    except ValueError:

        raise ValueError(
            "MAX_MESSAGES must be an integer"
        )

    use_s3 = (
        os.getenv(
            "USE_S3",
            "false"
        ).lower()
        in {"true", "1", "yes"}
    )

    s3_bucket = os.getenv(
        "S3_BUCKET",
        "ml-recommendation-raw"
    )

    logger.info("=" * 70)
    logger.info(
        "ML Recommendation Platform - Event Ingestion"
    )
    logger.info("=" * 70)

    logger.info(
        "Kafka topic: %s",
        kafka_topic
    )

    logger.info(
        "Output path: %s",
        output_path
    )

    logger.info(
        "File format: %s",
        file_format
    )

    logger.info(
        "Maximum messages: %d",
        max_messages
    )

    logger.info(
        "S3 enabled: %s",
        use_s3
    )

    if use_s3:
        logger.info(
            "S3 bucket: %s",
            s3_bucket
        )

    try:

        output_location = consume_and_store(
            kafka_topic=kafka_topic,
            output_path=output_path,
            file_format=file_format,
            max_messages=max_messages,
            use_s3=use_s3,
            s3_bucket=s3_bucket,
        )

        logger.info("=" * 70)
        logger.info(
            "SUCCESS"
        )
        logger.info(
            "Output: %s",
            output_location
        )
        logger.info("=" * 70)

    except Exception:

        logger.exception(
            "Event ingestion failed"
        )

        raise


if __name__ == "__main__":
    main()
