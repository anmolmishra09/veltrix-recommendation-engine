# System Design

## Overview

The ML Recommendation Platform is an end-to-end recommendation system for e-commerce applications. It implements a two-stage architecture (candidate generation + ranking) and is designed to be scalable, fault-tolerant, and easy to extend.

## Components

1. **Event Ingestion** - Apache Kafka for real-time event processing
2. **Feature Store** - Feast for managing and serving features
3. **Candidate Generation** - Embedding-based and popularity-based candidate generators
4. **Ranking** - Machine learning model to score candidates
5. **Filtering** - Post-processing to remove unavailable/duplicate items and apply business rules
6. **API Service** - FastAPI service that exposes recommendation endpoints
7. **Monitoring** - Prometheus, Grafana, and OpenTelemetry for observability
8. **Orchestration** - Apache Airflow for workflow scheduling
9. **Experiment Tracking** - MLflow for model versioning and experimentation

## Data Flow

1. User events (views, clicks, purchases) are ingested via Kafka.
2. Events are processed by Spark/Flink jobs to update feature tables in the feature store.
3. When a recommendation request is made:
   - The API retrieves user features from the feature store.
   - Candidate generators produce a set of candidate products.
   - The ranking model scores each candidate.
   - The filtering step removes unavailable/duplicate items and applies business rules.
   - The top-K recommendations are returned to the user.

## Deployment

The platform is designed to be deployed on Kubernetes using Helm charts. Infrastructure can be provisioned using Terraform.

## Scalability

- Kafka allows for horizontal scaling of event ingestion.
- The feature store can be scaled by adding more Redis instances or increasing the online store capacity.
- The API service can be scaled horizontally behind a load balancer.
- Candidate generation and ranking can be optimized by caching embeddings and using approximate nearest neighbor search (not implemented in this version).

## Extensibility

- New candidate generators can be added by implementing the CandidateGenerator interface.
- New ranking models can be swapped out by updating the MLflow model.
- New filtering rules can be added without changing the core recommendation logic.