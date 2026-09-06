# Monitoring

## Overview

Monitoring is essential for ensuring the health, performance, and correctness of the ML Recommendation Platform. We use a combination of open-source tools to collect, store, and visualize metrics, logs, and traces.

## Components

### Metrics Collection
- **Prometheus**: Collects and stores time-series metrics from services.
- **Node Exporter**: Collects host-level metrics (CPU, memory, disk, network).
- **Kube State Metrics**: Collects Kubernetes cluster metrics.
- **Application Metrics**: Instrumented using Prometheus client libraries in Python (for FastAPI) and Java (for Kafka consumers).

### Log Aggregation
- **Elasticsearch**: Stores and indexes log data.
- **Logstash**: Processes and enriches logs.
- **Kibana**: Provides a web interface for searching and visualizing logs.
- **Fluentd**: Agent that collects logs from containers and forwards to Logstash.

### Distributed Tracing
- **Jaeger**: Traces requests as they propagate through services.
- **OpenTelemetry**: SDKs and APIs for instrumenting code to generate traces.

### Visualization and Alerting
- **Grafana**: Creates dashboards from Prometheus and other data sources.
- **Alertmanager**: Handles alerts sent by Prometheus and routes them to notifications (email, Slack, PagerDuty).
- **Evidently**: Monitors data drift and model performance (integrated with MLflow).

## Key Metrics

### Infrastructure Metrics
- CPU utilization, memory usage, disk I/O, network bandwidth.
- Kubernetes pod restarts, crash loops, and scheduling delays.
- Kafka consumer lag and broker health.

### Application Metrics
- **Request Latency**: Time to serve API requests (broken down by endpoint).
- **Request Rate**: Number of requests per second.
- **Error Rate**: Percentage of requests resulting in errors (HTTP 5xx).
- **Cache Hit Ratio**: Percentage of feature store requests served from cache.
- **Model Inference Latency**: Time to run the ranking model.
- **Candidate Generation Latency**: Time to generate candidates.
- **Feature Store Latency**: Time to retrieve features from the online store.

### Business Metrics
- **Click-Through Rate (CTR)**: Percentage of recommendations that are clicked.
- **Conversion Rate**: Percentage of recommendations that lead to a purchase.
- **Revenue per Recommendation**: Average revenue generated from a recommendation.
- **Coverage**: Percentage of the catalog that is recommended over a period.
- **Diversity**: Measure of how varied the recommendations are (e.g., number of unique categories).

### Model Metrics
- **Data Drift**: Changes in the distribution of input features over time.
- **Concept Drift**: Changes in the relationship between features and the target variable.
- **Prediction Distribution**: Distribution of model output scores.
- **Feature Importance**: Changes in which features are most influential.

## Alerting Rules

### Critical Alerts (Page Immediately)
- API error rate > 5% for 5 minutes.
- Recommendation latency > 100ms for 5 minutes.
- Feature store unavailable for 2 minutes.
- Kafka consumer lag > 100,000 messages for 10 minutes.
- Disk usage > 90% on any critical volume.

### Warning Alerts (Notify for Investigation)
- API error rate > 2% for 15 minutes.
- Recommendation latency > 50ms for 15 minutes.
- CPU utilization > 80% for 30 minutes.
- Memory utilization > 85% for 30 minutes.
- Model prediction distribution has shifted significantly (KS test p-value < 0.01).

## Logs Structure

### Application Logs
- Structured as JSON for easy parsing.
- Include fields: timestamp, service name, log level, message, trace ID, span ID, user ID (if available), request ID.
- Example:
  ```json
  {
    "timestamp": "2026-09-03T10:30:00Z",
    "service": "recommendation-api",
    "level": "ERROR",
    "message": "Failed to retrieve user features",
    "trace_id": "abc123",
    "span_id": "def456",
    "user_id": "user_123",
    "request_id": "xyz789",
    "stack_trace": "..."
  }
  ```

### Access Logs
- Record each API request.
- Include fields: timestamp, method, path, status code, response time, user ID, IP address, user agent.

## Tracing

- Each incoming request is assigned a unique trace ID.
- As the request flows through services (API -> feature store -> model loader -> etc.), spans are created.
- Span attributes include operation name, start time, end time, status, and custom attributes (e.g., user ID, candidate count).
- Traces are exported to Jaeger via the OpenTelemetry collector.

## Implementation Details

### Prometheus Instrumentation
- The FastAPI application uses the `prometheus-fastapi-instrumentator` package to expose metrics at `/metrics`.
- Custom metrics are defined using the `prometheus_client` library.

### Log Collection
- Each container writes logs to stdout/stderr.
- Fluentd agents running on each node collect logs and forward them to Logstash.
- Logstash applies filters (e.g., adding GeoIP information) and indexes logs in Elasticsearch.

### Tracing Setup
- OpenTelemetry SDK is initialized in each service.
- The SDK is configured to export traces to the Jaeger agent running as a sidecar.
- Automatic instrumentation is used for popular libraries (e.g., requests, psycopg2).

### Evidently Integration
- Evidently runs as a scheduled job (via Airflow) to compare current production data with training data.
- Reports are uploaded to MLflow as artifacts and can be visualized in the MLflow UI.
- Alerts are triggered if data drift or performance degradation exceeds thresholds.

## Dashboards

### Overview Dashboard
- Shows overall system health: request rate, error rate, latency.
- Includes infrastructure metrics: CPU, memory, disk, network.

### Service Dashboard
- Breaks down metrics by service: API, feature store, model loader, etc.
- Shows latency and error rates for each service.

### Business Dashboard
- Shows CTR, conversion rate, revenue, coverage, diversity.
- Compares current performance to historical baselines.

### Model Dashboard
- Shows data drift metrics, concept drift metrics, prediction distribution.
- Compares current model performance to the baseline model.

## Security Considerations

- Metrics and logs may contain sensitive information (e.g., user IDs, product IDs).
- Access to Grafana, Kibana, and Jaeger UI is restricted via authentication and authorization.
- Logs are redacted to remove personally identifiable information (PII) before storage.
- Network traffic between monitoring components is encrypted where possible.

## Cost Optimization

- Retention policies are set for Prometheus (15 days), Elasticsearch (30 days), and Jaeger (7 days).
- Downsampling is applied to high-cardinality metrics in Prometheus.
- Inactive indices in Elasticsearch are migrated to cheaper storage tiers.