#!/bin/bash
# Submit a Spark job to the Spark cluster

set -e

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <spark-application-jar-or-python-file> [spark-args]"
    echo "Example: $0 ./ml/spark_job.py"
    exit 1
fi

APP=$1
shift

# Wait for Spark master to be ready
echo "Waiting for Spark master to be ready..."
until nc -z localhost 7077; do
    sleep 0.1
done
echo "Spark master is ready!"

# Submit the job
echo "Submitting Spark job: $APP"
spark-submit \
    --master spark://spark-master:7077 \
    "$APP" \
    "$@"

echo "Spark job submitted."