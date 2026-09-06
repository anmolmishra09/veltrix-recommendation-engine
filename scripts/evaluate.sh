#!/bin/bash
# Evaluate models for the ML Recommendation Platform

set -e

echo "Starting model evaluation..."

# Change to the ml directory
cd ml

# Run the evaluation script
python3 evaluate.py "$@"

echo "Model evaluation completed."