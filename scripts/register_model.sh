#!/bin/bash
# Register a model with MLflow

set -e

echo "Registering model with MLflow..."

# Change to the ml directory
cd ml

# Run the registration script
python3 register_model.py "$@"

echo "Model registration completed."