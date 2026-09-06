# ML Recommendation Platform

An end-to-end recommendation and ranking platform for e-commerce applications.

## Overview

This platform implements a modern, scalable recommendation system with a two-stage architecture (candidate generation + ranking) using a robust technology stack:

**Backend**: Python 3.9+, FastAPI, PostgreSQL, Redis, Kafka, Feast, MLflow, Spark, Airflow
**ML**: XGBoost, LightGBM, PyTorch, scikit-learn, pandas, numpy
**Infrastructure**: Docker, Docker Compose, Prometheus, Grafana, OpenTelemetry
**Monitoring**: Prometheus, Grafana, OpenTelemetry, Evidently for drift detection
**Orchestration**: Apache Airflow
**Testing**: pytest, pytest-asyncio, Locust

## Key Features

- **Event-driven architecture** with Apache Kafka for real-time event ingestion
- **Two-stage recommendation system**:
  - Stage 1: Candidate generation using collaborative filtering, content-based, popularity, and embedding-based approaches
  - Stage 2: Ranking using interchangeable XGBoost, LightGBM, and neural network models
- **Feature store** using Feast for consistent feature serving between training and inference
- **Model tracking and experiment management** with MLflow
- **Real-time inference API** with FastAPI
- **Cold start handling** for new users and products
- **A/B testing framework** for experimentation
- **Comprehensive monitoring** with Prometheus, Grafana, and OpenTelemetry
- **Workflow orchestration** with Apache Airflow
- **Data validation and preprocessing pipeline**
- **Model evaluation** with offline metrics (Precision@K, NDCG, MAP, etc.)
- **Data drift detection** using Evidently

## Architecture

```
E-COMMERCE WEBSITE
        |
        | User clicks / views / searches / buys
        v
     Event API (Kafka Producer)
        |
        v
      Kafka Topics (user-events, product-events, etc.)
        |
        +---------------------+
        |                     |
        v                     v
   Spark Batch              S3/MinIO (Data Lake)
   Processing               (raw events)
        |                     |
        v                     |
 Feature Generation         |
        |                     |
        v                     |
     Feast <-----------------+
        |                     |
        v                     |
 Training Dataset           |
        |                     |
        v                     |
    ML Training              |
        |                     |
        v                     |
   MLflow Model Registry     |
        |                     |
        v                     |
   Model Deployment          |
        |                     |
        v                     |
  FastAPI + Redis Cache      |
        |                     |
        v                     |
  Recommendation Request     |
        |                     |
        v                     |
  Candidate Generation       |
        |                     |
        v                     |
   Rank Products             |
        |                     |
        v                     |
   Top-K Recommendations     |
        |                     |
        v                     |
   User / Frontend           |
        |                     |
        v                     |
  New Interaction -----------> Kafka
```

## Getting Started

### Prerequisites
- Docker and Docker Compose (version 2.0+)
- Git
- Approximately 8GB+ RAM available for Docker containers

### Quick Start

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be healthy** (2-5 minutes):
   ```bash
   docker-compose ps
   ```
   All services should show "healthy" or "Up"

3. **Access the services**:
   - **API Documentation**: http://localhost:8000/docs
   - **Frontend Demo**: http://localhost
   - **MLflow UI**: http://localhost:5000
   - **Grafana Dashboard**: http://localhost:3000 (login: admin/admin)
   - **Prometheus**: http://localhost:9090
   - **Airflow**: http://localhost:8080 (login: admin/admin)

4. **Generate initial demo data** (optional):
   ```bash
   python scripts/generate_demo_data.py
   ```

5. **Train the models** via Airflow:
   - Access Airflow at http://localhost:8080
   - Trigger the `training_dag` DAG
   - Wait for completion (check logs for details)

6. **Get recommendations** (example):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/recommendations/" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "user_1",
       "context": {"source": "homepage", "device": "desktop"},
       "candidate_limit": 100,
       "top_k": 10,
       "ranking_model": "xgboost"
     }'
   ```

## Technology Stack

### Core Components
- **API**: FastAPI with Pydantic models
- **Database**: PostgreSQL 15 (users, products, interactions, experiments, recommendations)
- **Cache**: Redis 7 (recommendation caching, hot features)
- **Streaming**: Apache Kafka 3.x (event ingestion)
- **Object Storage**: MinIO (S3-compatible, for MLflow artifacts, data lake)
- **Feature Store**: Feast 0.40+ (feature serving)
- **ML Frameworks**: 
  - XGBoost 2.0+ (ranking)
  - LightGBM 4.5+ (ranking)
  - PyTorch 2.3+ (neural ranking/embeddings)
  - scikit-learn 1.4+ (metrics, utilities)
  - pandas 2.2+, numpy 1.26+ (data manipulation)
- **Experiment Tracking**: MLflow 2.12+
- **Orchestration**: Apache Airflow 2.8+ with Postgres and Spark providers
- **Monitoring**: 
  - Prometheus (metrics collection)
  - Grafana (dashboards)
  - OpenTelemetry (distributed tracing)
  - Evidently (data drift detection)
- **Data Engineering**: 
  - PySpark 3.5+ (batch processing)
  - Apache Kafka (event streaming)
- **Testing**: pytest, pytest-asyncio, Locust (load testing)
- **Infrastructure**: Docker, Docker Compose

### ML Algorithms Implemented
- **Candidate Generation**:
  - Collaborative Filtering (user-item matrix factorization)
  - Content-Based Filtering (item-item similarity)
  - Popularity-Based (with time decay)
  - Embedding Similarity (user-product embedding dot product)
  - Hybrid Combination (configurable weights)
- **Ranking Models**:
  - XGBoost Ranker (`rank:pairwise` objective)
  - LightGBM Ranker (`lambdarank` objective)
  - Neural Ranker (PyTorch MLP with ReLU activations)
  - Hybrid Ranking (configurable model selection)

## Project Structure

```
ml-recommendation-platform/
├── apps/                    # Production applications
│   ├── api/                 # FastAPI recommendation service
│   ├── consumer/            # Kafka consumers (placeholders)
│   └── frontend/            # HTML/JavaScript demo frontend
├── database/                # Database schemas, seeds, migrations
├── data/                    # Data pipeline directories
│   ├── raw/                 # Raw ingested data
│   ├── validation/          # Validated data (schema checks)
│   ├── preprocessing/       # Preprocessed data (cleaning)
│   ├── processed/           # Cleaned data
│   └── features/            # Engineered features (user/product)
├── dags/                    # Airflow DAGs for orchestration
├── ml/                      # Machine learning logic
│   ├── embeddings/          # Embedding generation and similarity
│   │   ├── base.py          # Base embedding interface
│   │   ├── product_embeddings.py
│   │   ├── user_embeddings.py
│   │   └── similarity.py    # Cosine similarity, etc.
│   ├── recommendation/      # Recommendation algorithms
│   │   ├── candidate_generation/
│   │   │   ├── base.py          # Base candidate generator
│   │   │   ├── collaborative.py # Collaborative filtering
│   │   │   ├── content.py       # Content-based
│   │   │   ├── embedding_based.py # Embedding similarity
│   │   │   ├── popularity.py    # Popularity-based
│   │   │   └── hybrid.py        # Hybrid candidate generator
│   │   ├── ranking/
│   │   │   ├── base.py          # Base ranker
│   │   │   ├── xgboost_ranker.py
│   │   │   ├── lightgbm_ranker.py
│   │   │   ├── neural_ranker.py
│   │   │   └── ranker.py        # Ranker wrapper
│   │   └── hybrid.py          # Hybrid recommender (combines sources)
│   ├── cold_start/          # Cold start handling
│   └── utils/               # ML utilities
├── monitoring/              # Monitoring configurations
│   ├── prometheus/          # Prometheus config
│   ├── grafana/             # Grafana dashboards
│   ├── opentelemetry/       # OpenTelemetry config
│   └── evidently/           # Evidently drift detection
├── pipelines/               # Data and ML pipelines
│   ├── ingestion/           # Data ingestion (Kafka to S3)
│   ├── preprocessing/       # Data validation and cleaning
│   ├── feature_engineering/ # Feature generation (Spark/Pandas)
│   ├── training/            # Model training scripts
│   └── evaluation/          # Model evaluation scripts
├── tests/                   # Unit tests
├── docker-compose.yml       # Docker Compose orchestration
├── requirements.txt         # Python dependencies
├── alembic.ini              # Alembic migration configuration
├── FINAL_SUMMARY.md         # This summary document
└── README.md                # This file
```

## API Endpoints

### Health Checks
- `GET /health` - Returns `{"status": "healthy"}`
- `GET /health/ready` - Checks DB and Redis connectivity

### Recommendations
- `POST /api/v1/recommendations/` 
  - **Request**: `{user_id, context?, candidate_limit?, top_k?, ranking_model?}`
  - **Response**: `{recommendations: [{item_id, score, rank, source}], user_id, context, ranking_model_used, latency_ms, metadata}`

### Ranking
- `POST /api/v1/ranking/`
  - **Request**: `{user_id, item_ids, context?, model_type?}`
  - **Response**: `{rankings: [{item_id, score, rank}], user_id, model_used, latency_ms}`

### Event Ingestion
- `POST /api/v1/events/`
  - **Request**: `{user_id, product_id, event_type, timestamp?, session_id?, context?, metadata?}`
  - **Response**: `{status, message, event_id}`

### Entity Lookup
- `GET /api/v1/users/{user_id}` - User details
- `GET /api/v1/products/{product_id}` - Product details
- `GET /api/v1/experiments/{experiment_id}` - Experiment details

### Admin
- `GET /api/v1/admin/models` - List available models
- `GET /api/v1/admin/metrics` - System metrics
- `POST /api/v1/admin/reload_model/{model_name}` - Reload model (placeholder)

## Configuration

### Environment Variables
Set via `.env` file or Docker Compose:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `FEAST_FEATURE_STORE_PATH`: Path to Feast repository
- `MLFLOW_TRACKING_URI`: MLflow tracking server URL
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `ENABLE_TELEMETRY`: Enable OpenTelemetry instrumentation
- `DEBUG`: Enable debug logging

### Model Weights
The hybrid recommender uses configurable weights:
- Collaborative filtering: 0.35 (default)
- Content-based: 0.25 (default)
- Popularity: 0.15 (default)
- Embedding similarity: 0.25 (default)

Weights are normalized to sum to 1.0.

## Customization

### Adding New Candidate Generators
1. Inherit from `ml.recommendation.candidate_generation.base.CandidateGenerator`
2. Implement the `generate(user_id, context, limit)` method
3. Register the generator in the hybrid candidate generator

### Adding New Ranking Models
1. Inherit from `ml.ranking.base.BaseRanker`
2. Implement `train(X, y)`, `predict(X)`, `save(path)`, `load(path)` methods
3. Update the `RankerWrapper` to handle the new model type

### Changing Hybrid Weights
Modify the `HybridRecommender` initialization in the API or create a new instance with custom weights:
```python
recommender = HybridRecommender(
    collaborative_weight=0.4,
    content_weight=0.2,
    popularity_weight=0.1,
    embedding_weight=0.3
)
```

## Monitoring and Observability

### Metrics Exposed
The API exposes Prometheus metrics at `/metrics` endpoint:
- HTTP request counts and durations
- Recommendation request counts and latencies
- Cache hit/miss ratios
- Model prediction latencies
- Custom business metrics (to be implemented)

### Dashboards
Grafana dashboards include:
- System overview (API latency, error rates)
- Infrastructure health (Kafka lag, Redis memory, DB connections)
- Model performance (prediction latency, feature freshness)
- Recommendation quality (CTR, conversion placeholders)

### Tracing
OpenTelemetry instrumentation provides:
- Distributed tracing across API calls
- Database query tracing
- Redis operation tracing
- Kafka produce/consume tracing

## Data Pipeline

### Stages
1. **Ingestion**: Kafka consumers write raw events to S3/MinIO (JSON/Parquet)
2. **Validation**: Schema validation, anomaly detection, error reporting
3. **Preprocessing**: Cleaning, deduplication, handling missing values
4. **Feature Engineering**: Spark jobs generate user/product features
5. **Feature Store**: Features written to Feast for online/offline serving
6. **Training**: Training dataset generation from features + interactions
7. **Model Training**: XGBoost, LightGBM, and neural network models
8. **Evaluation**: Offline metrics (Precision@K, NDCG, MAP, etc.)
9. **Deployment**: Model registration in MLflow, API deployment

### Supported Formats
- CSV (initial loading, small datasets)
- JSON (Kafka ingestion, intermediate storage)
- Parquet (efficient columnar storage for features)
- Pickle (model serialization)

## Testing

Run unit tests:
```bash
python -m pytest tests/
```

Run specific test modules:
```bash
python -m pytest tests/test_recommender.py -v
```

## Production Considerations

For production deployment, consider:

1. **Security**:
   - Implement proper authentication (JWT, OAuth2, or API keys)
   - Add authorization controls (RBAC)
   - Enable TLS encryption for all service communications
   - Use secrets management (HashiCorp Vault, AWS Secrets Manager)
   - Regular security scanning and updates

2. **Scalability**:
   - Tune Kafka partitioning (align with consumer parallelism)
   - Increase Spark executor memory and cores for larger datasets
   - Implement model quantization (INT8/FP16) for serving efficiency
   - Add horizontal pod autoscaling for API consumers
   - Implement read replicas for PostgreSQL

3. **Reliability**:
   - Add circuit breakers (Hystrix/resilience4j pattern)
   - Implement proper error handling and retry logic with exponential backoff
   - Add dead letter queues for failed event processing
   - Implement backup and disaster recovery procedures
   - Add health checks and liveness/readiness probes
   - Implement automated failover for critical services

4. **Data Quality**:
   - Add schema validation with Apache Avro or Protobuf for Kafka events
   - Implement data quality monitoring (null rates, distribution changes)
   - Add automated data quality alerts
   - Implement data lineage tracking

5. **ML Operations**:
   - Implement automated model retraining based on performance degradation
   - Add canary testing for model deployments
   - Implement model explainability (SHAP, LIME) for debugging
   - Add feature importance tracking over time
   - Implement multi-armed bandit exploration for cold start mitigation

6. **Observability Enhancements**:
   - Add business metrics (CTR, conversion rate, revenue per recommendation)
   - Implement model drift detection with scheduled Evidently jobs
   - Add log aggregation (ELK stack or Loki/Promtail)
   - Implement synthetic transaction monitoring (heartbeat events)
   - Add service mesh (Istio/Linkerd) for advanced traffic management

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with inspiration from:
- Netflix Prize and recommendation system literature
- Airbnb's Hopsworks feature store
- Uber's Michelangelo ML platform
- LinkedIn's Prototype feature store
- Google's Wide & Deep learning for recommendations
- Various open-source recommendation systems (LightFM, Surprise, implicit)

Enjoy building intelligent recommendation experiences!