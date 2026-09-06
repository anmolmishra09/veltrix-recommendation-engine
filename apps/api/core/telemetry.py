"""
OpenTelemetry configuration.
"""
from .config import settings
import logging

logger = logging.getLogger(__name__)

def setup_telemetry():
    """
    Setup OpenTelemetry if enabled.
    """
    if not settings.ENABLE_TELEMETRY:
        logger.info("Telemetry is disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())

        # Configure OTLP exporter (assuming Jaeger or similar via OTLP)
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_ENDPOINT", "http://jaeger:4317"),
            insecure=True
        )

        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Instrument FastAPI
        FastAPIInstrumentor().instrument()

        # Instrument Redis
        RedisInstrumentor().instrument()

        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()

        logger.info("OpenTelemetry configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}")
        # Disable telemetry if setup fails
        settings.ENABLE_TELEMETRY = False