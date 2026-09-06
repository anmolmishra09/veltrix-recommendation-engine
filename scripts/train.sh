#!/bin/bash
# Train models for the ML Recommendation Platform

set -e

echo "Starting model training..."

# Change to the ml directory
cd ml

# Run the training script
python3 train.py "$@"

echo "Model training completed."