#!/bin/bash
# Start Airflow services

set -e

echo "Starting Airflow services..."

# Start Airflow webserver and scheduler using docker-compose
docker-compose up -d airflow-webflow airflow-scheduler

# Wait for them to be ready
echo "Waiting for Airflow to be ready..."
until nc -z localhost 8080; do
    sleep 0.1
done
echo "Airflow webserver is ready at http://localhost:8080"

echo "Airflow scheduler is running in the background."

echo "To stop Airflow, run: docker-compose down airflow-webserver airflow-scheduler"