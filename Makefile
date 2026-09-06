# Makefile for ML Recommendation Platform
# Provides convenient commands for development, testing, and deployment.

# Variables
PYTHON = python3
PIP = pip
DOCKER = docker
KUBECTL = kubectl
HELM = helm
TERRAFORM = terraform

# Directories
API_DIR = apps/api
FRONTEND_DIR = apps/frontend
ML_DIR = ml
INFRA_DIR = infrastructure
SCRIPTS_DIR = scripts

# Default target
.PHONY: help
help:
	@echo "ML Recommendation Platform Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup          Install development dependencies"
	@echo "  install        Install production dependencies"
	@echo "  dev            Start development services (API, frontend)"
	@echo "  test           Run unit tests"
	@echo "  test-integ     Run integration tests"
	@echo "  lint           Run linter (flake8)"
	@echo "  format         Format code (black)"
	@echo "  type-check     Run type checker (mypy)"
	@echo "  api            Start the API service"
	@echo "  frontend       Start the frontend development server"
	@echo "  train          Train models"
	@echo "  evaluate       Evaluate models"
	@echo "  register       Register model with MLflow"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-up      Start services with Docker Compose"
	@echo "  docker-down    Stop Docker Compose services"
	@echo "  kafka-start    Start Kafka (for development)"
	@echo "  kafka-stop     Stop Kafka"
	@echo "  spark-submit   Submit a Spark job"
	@echo "  airflow-start  Start Airflow webserver and scheduler"
	@echo "  airflow-stop   Stop Airflow"
	@echo "  seed-data      Seed the database with initial data"
	@echo "  migrate-db     Run database migrations"
	@echo "  clean          Remove temporary files and caches"
	@echo ""

# Development setup
.PHONY: setup
setup:
	$(PIP) install --upgrade $(PIP)
	$(PIP) install -r requirements.txt
	$(PIP) install flake8 black mypy pytest pytest-asyncio

# Production install
.PHONY: install
install:
	$(PIP) install --upgrade $(PIP)
	$(PIP) install -r requirements.txt

# Start development services
.PHONY: dev
dev:
	@echo "Starting development services..."
	@echo "API will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	$(PYTHON) $(API_DIR)/main.py &
	cd $(FRONTEND_DIR) && npm start

# Start API service
.PHONY: api
api:
	$(PYTHON) $(API_DIR)/main.py

# Start frontend development server
.PHONY: frontend
frontend:
	cd $(FRONTEND_DIR) && npm start

# Run unit tests
.PHONY: test
test:
	pytest tests/unit/ -v

# Run integration tests
.PHONY: test-integ
test-integ:
	pytest tests/integration/ -v

# Run linter
.PHONY: lint
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
.PHONY: format
format:
	black .

# Type check
.PHONY: type-check
type-check:
	mypy .

# Train models
.PHONY: train
train:
	$(PYTHON) $(ML_DIR)/train.py

# Evaluate models
.PHONY: evaluate
evaluate:
	$(PYTHON) $(ML_DIR)/evaluate.py

# Register model with MLflow
.PHONY: register
register:
	$(PYTHON) $(ML_DIR)/register_model.py

# Build Docker images
.PHONY: docker-build
docker-build:
	$(DOCKER) build -t ml-recommendation-platform:api $(API_DIR)
	$(DOCKER) build -t ml-recommendation-platform:frontend $(FRONTEND_DIR)

# Start services with Docker Compose
.PHONY: docker-up
docker-up:
	docker-compose up

# Stop Docker Compose services
.PHONY: docker-down
docker-down:
	docker-compose down

# Start Kafka (for development)
.PHONY: kafka-start
kafka-start:
	@echo "Starting Kafka and Zookeeper..."
	docker-compose -f docker-compose.yml up -d zookeeper kafka

# Stop Kafka
.PHONY: kafka-stop
kafka-stop:
	@echo "Stopping Kafka and Zookeeper..."
	docker-compose -f docker-compose.yml down zookeeper kafka

# Submit a Spark job
.PHONY: spark-submit
spark-submit:
	spark-submit --master local[*] $(ML_DIR)/spark_job.py

# Start Airflow webserver and scheduler
.PHONY: airflow-start
airflow-start:
	airflow webserver --port 8080 &
	airflow scheduler

# Stop Airflow
.PHONY: airflow-stop
airflow-stop:
	pkill -f "airflow webserver"
	pkill -f "airflow scheduler"

# Seed the database with initial data
.PHONY: seed-data
seed-data:
	$(PYTHON) $(SCRIPTS_DIR)/seed_data.py

# Run database migrations
.PHONY: migrate-db
migrate-db:
	$(PYTHON) $(SCRIPTS_DIR)/migrate_db.py

# Clean temporary files and caches
.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Help (default)
.PHONY: help
help:
	@echo "ML Recommendation Platform Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup          Install development dependencies"
	@echo "  install        Install production dependencies"
	@echo "  dev            Start development services (API, frontend)"
	@echo "  test           Run unit tests"
	@echo "  test-integ     Run integration tests"
	@echo "  lint           Run linter (flake8)"
	@echo "  format         Format code (black)"
	@echo "  type-check     Run type checker (mypy)"
	@echo "  api            Start the API service"
	@echo "  frontend       Start the frontend development server"
	@echo "  train          Train models"
	@echo "  evaluate       Evaluate models"
	@echo "  register       Register model with MLflow"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-up      Start services with Docker Compose"
	@echo "  docker-down    Stop Docker Compose services"
	@echo "  kafka-start    Start Kafka (for development)"
	@echo "  kafka-stop     Stop Kafka"
	@echo "  spark-submit   Submit a Spark job"
	@echo "  airflow-start  Start Airflow webserver and scheduler"
	@echo "  airflow-stop   Stop Airflow"
	@echo "  seed-data      Seed the database with initial data"
	@echo "  migrate-db     Run database migrations"
	@echo "  clean          Remove temporary files and caches"
	@echo ""