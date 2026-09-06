#!/bin/bash
# Setup script for ML Recommendation Platform
# Installs dependencies and prepares the development environment.

set -e  # Exit on any error

echo "Setting up ML Recommendation Platform..."

# Check if Python 3.9+ is installed
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
if (( $(echo "$python_version < 3.9" | bc -l) )); then
    echo "Error: Python 3.9+ is required. Found Python $python_version"
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt
python3 -m pip install flake8 black mypy pytest pytest-asyncio

# Check if Node.js is installed (for frontend)
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js not found. Please install Node.js 14+ to run the frontend."
else
    echo "Node.js found: $(node --version)"
    # Install frontend dependencies
    echo "Installing frontend dependencies..."
    cd apps/frontend && npm install
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker not found. Please install Docker to use containerized services."
else
    echo "Docker found: $(docker --version)"
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Warning: kubectl not found. Please install kubectl to interact with Kubernetes."
else
    echo "kubectl found: $(kubectl version --client)"
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Warning: Helm not found. Please install Helm to deploy charts."
else
    echo "Helm found: $(helm version)"
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Warning: Terraform not found. Please install Terraform to provision infrastructure."
else
    echo "Terraform found: $(terraform version)"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p models
mkdir -p logs
mkdir -p data

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in the required values"
echo "  2. For local development: make dev"
echo "  3. For Docker Compose: make docker-up"
echo "  4. To run tests: make test"
echo ""