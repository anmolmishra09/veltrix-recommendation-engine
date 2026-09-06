"""
Monitoring module for Prometheus metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import logging
import time
import psutil
import os
from typing import Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# System Monitoring Metrics
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage', registry=REGISTRY)
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage', registry=REGISTRY)
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage', registry=REGISTRY)

# API Monitoring Metrics
API_REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status_code'], registry=REGISTRY)
API_REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'API request latency', ['method', 'endpoint'], buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10), registry=REGISTRY)
API_REQUEST_SIZE = Histogram('api_request_size_bytes', 'API request size in bytes', ['method', 'endpoint'], registry=REGISTRY)
API_RESPONSE_SIZE = Histogram('api_response_size_bytes', 'API response size in bytes', ['method', 'endpoint'], registry=REGISTRY)

# ML Monitoring Metrics
ML_MODEL_PREDICTION_COUNT = Counter('ml_model_predictions_total', 'Total ML model predictions', ['model_name', 'model_version'], registry=REGISTRY)
ML_MODEL_PREDICTION_LATENCY = Histogram('ml_model_prediction_duration_seconds', 'ML model prediction latency', ['model_name', 'model_version'], buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5), registry=REGISTRY)
ML_FEATURE_DRIFT_SCORE = Gauge('ml_feature_drift_score', 'Feature drift score', ['feature_name'], registry=REGISTRY)
ML_DATA_DRIFT_SCORE = Gauge('ml_data_drift_score', 'Data drift score', ['dataset_name'], registry=REGISTRY)
ML_MODEL_PERFORMANCE = Gauge('ml_model_performance_score', 'Model performance score', ['model_name', 'metric_name'], registry=REGISTRY)

# Business Monitoring Metrics
BUSINESS_CTR = Gauge('business_ctr', 'Click-through rate', ['experiment_id', 'variant'], registry=REGISTRY)
BUSINESS_CONVERSION_RATE = Gauge('business_conversion_rate', 'Conversion rate', ['experiment_id', 'variant'], registry=REGISTRY)
BUSINESS_REVENUE_PER_RECOMMENDATION = Gauge('business_revenue_per_recommendation', 'Revenue per recommendation', ['experiment_id', 'variant'], registry=REGISTRY)
BUSINESS_ADD_TO_CART_RATE = Gauge('business_add_to_cart_rate', 'Add-to-cart rate', ['experiment_id', 'variant'], registry=REGISTRY)
BUSINESS_COVERAGE = Gauge('business_coverage', 'Recommendation coverage', ['experiment_id'], registry=REGISTRY)
BUSINESS_DIVERSITY = Gauge('business_diversity', 'Recommendation diversity', ['experiment_id'], registry=REGISTRY)

class MonitoringService:
    def __init__(self):
        self.start_time = time.time()
        logger.info("Monitoring service initialized")

    def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            SYSTEM_CPU_USAGE.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            SYSTEM_DISK_USAGE.set(disk_percent)
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    def record_api_request(self, method: str, endpoint: str, status_code: int,
                          request_size: int = 0, response_size: int = 0):
        """Record API request metrics."""
        API_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        API_REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(request_size)
        API_RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(response_size)

    def time_api_request(self, method: str, endpoint: str):
        """Decorator to time API requests."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    status_code = getattr(result, 'status_code', 200)
                    return result
                except Exception as e:
                    status_code = 500
                    raise e
                finally:
                    duration = time.time() - start_time
                    API_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            return wrapper
        return decorator

    def record_ml_prediction(self, model_name: str, model_version: str, latency: float):
        """Record ML model prediction metrics."""
        ML_MODEL_PREDICTION_COUNT.labels(model_name=model_name, model_version=model_version).inc()
        ML_MODEL_PREDICTION_LATENCY.labels(model_name=model_name, model_version=model_version).observe(latency)

    def update_feature_drift(self, feature_name: str, drift_score: float):
        """Update feature drift metric."""
        ML_FEATURE_DRIFT_SCORE.labels(feature_name=feature_name).set(drift_score)

    def update_data_drift(self, dataset_name: str, drift_score: float):
        """Update data drift metric."""
        ML_DATA_DRIFT_SCORE.labels(dataset_name=dataset_name).set(drift_score)

    def update_model_performance(self, model_name: str, metric_name: str, score: float):
        """Update model performance metric."""
        ML_MODEL_PERFORMANCE.labels(model_name=model_name, metric_name=metric_name).set(score)

    def update_business_metrics(self, experiment_id: str, variant: str, metrics: Dict[str, float]):
        """Update business metrics."""
        if 'ctr' in metrics:
            BUSINESS_CTR.labels(experiment_id=experiment_id, variant=variant).set(metrics['ctr'])
        if 'conversion_rate' in metrics:
            BUSINESS_CONVERSION_RATE.labels(experiment_id=experiment_id, variant=variant).set(metrics['conversion_rate'])
        if 'revenue_per_recommendation' in metrics:
            BUSINESS_REVENUE_PER_RECOMMENDATION.labels(experiment_id=experiment_id, variant=variant).set(metrics['revenue_per_recommendation'])
        if 'add_to_cart_rate' in metrics:
            BUSINESS_ADD_TO_CART_RATE.labels(experiment_id=experiment_id, variant=variant).set(metrics['add_to_cart_rate'])
        if 'coverage' in metrics:
            BUSINESS_COVERAGE.labels(experiment_id=experiment_id).set(metrics['coverage'])
        if 'diversity' in metrics:
            BUSINESS_DIVERSITY.labels(experiment_id=experiment_id).set(metrics['diversity'])

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        # Update system metrics before returning
        self.update_system_metrics()
        return generate_latest(REGISTRY).decode('utf-8')

# Global monitoring service instance
monitoring_service = MonitoringService()

def setup_monitoring():
    """Setup monitoring - to be called on app startup."""
    logger.info("Monitoring setup complete")