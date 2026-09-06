#!/bin/bash
# Create Kafka topics for the ML Recommendation Platform

set -e

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
until nc -z localhost 9092; do
    sleep 0.1
done
echo "Kafka is ready!"

# Define topics
TOPICS=(
    "user_events"
    "product_events"
    "transaction_events"
    "recommendation_events"
    "model_metrics"
)

# Number of partitions and replication factor
PARTITIONS=3
REPLICATION_FACTOR=1

# Create each topic
for topic in "${TOPICS[@]}"; do
    echo "Creating topic: $topic"
    docker exec \
        $(docker ps -qf "name=kafka") \
        kafka-topics --create \
        --topic "$topic" \
        --partitions "$PARTITIONS" \
        --replication-factor "$REPLICATION_FACTOR" \
        --if-not-exists \
        --zookeeper localhost:2181
done

echo "All topics created successfully!"

# List topics to verify
echo "Listing topics:"
docker exec \
    $(docker ps -qf "name=kafka") \
    kafka-topics --list --zookeeper localhost:2181