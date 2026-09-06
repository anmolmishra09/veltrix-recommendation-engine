"""
OpenTelemetry observability implementation.
"""
import logging
import time
from typing import Callable
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

# Global tracer and meter
tracer = None
meter = None

def setup_telemetry():
    """
    Setup OpenTelemetry tracing and metrics.
    """
    global tracer, meter

    try:
        # Define service information
        service_name = "recommendation-platform"
        service_version = "0.1.0"

        # Create resource
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            "deployment.environment": "development"
        })

        # Setup tracing
        trace_provider = TracerProvider(resource=resource)
        otlp_trace_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",  # Default OTLP endpoint
            insecure=True
        )
        trace_provider.add_span_processor(
            BatchSpanProcessor(otlp_trace_exporter)
        )
        trace.set_tracer_provider(trace_provider)
        tracer = trace.get_tracer(__name__)

        # Setup metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint="http://localhost:4317",  # Default OTLP endpoint
                insecure=True
            ),
            export_interval_millis=5000
        )
        metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(metrics_provider)
        meter = metrics.get_meter(__name__)

        # Create useful metrics
        request_counter = meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )

        request_duration = meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration",
            unit="s"
        )

        recommendation_counter = meter.create_counter(
            name="recommendations_generated_total",
            description="Total number of recommendations generated",
            unit="1"
        )

        logger.info("OpenTelemetry setup complete")

    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        # Fallback to no-op implementation
        tracer = None
        meter = None

def trace_function(name: str = None):
    """
    Decorator to trace function execution.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if tracer is None:
                return func(*args, **kwargs)

            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                # Add function arguments as span attributes
                if args:
                    span.set_attribute("function.args", str(args))
                if kwargs:
                    span.set_attribute("function.kwargs", str(kwargs))

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", str(result)[:500])  # Limit length
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator

def trace_method(name: str = None):
    """
    Decorator to trace method execution (includes self/cls).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if tracer is None:
                return func(self, *args, **kwargs)

            span_name = name or f"{self.__class__.__name__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                # Add method arguments as span attributes
                if args:
                    span.set_attribute("method.args", str(args))
                if kwargs:
                    span.set_attribute("method.kwargs", str(kwargs))

                try:
                    result = func(self, *args, **kwargs)
                    span.set_attribute("method.result", str(result)[:500])  # Limit length
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator

def add_trace_context(**attributes):
    """
    Add attributes to the current span.
    """
    if tracer is None:
        return

    try:
        current_span = trace.get_current_span()
        if current_span:
            for key, value in attributes.items():
                current_span.set_attribute(key, value)
    except Exception as e:
        logger.debug(f"Could not add trace context: {e}")

def get_tracer():
    """Get the global tracer."""
    return tracer

def get_meter():
    """Get the global meter."""
    return meter