"""
Main FastAPI application.
"""
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.logging import setup_logging
from .core.telemetry import setup_telemetry, get_tracer
from .core.database import create_tables
from .core.monitoring import setup_monitoring, monitoring_service
from .core.config import settings
import logging

# Import services and repositories to ensure they're registered
from .core import services, repositories

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    debug=settings.api.debug
)

# Setup logging
setup_logging()

# Setup telemetry
setup_telemetry()

# Setup monitoring
setup_monitoring()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument with OpenTelemetry
try:
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    # RedisInstrumentor().instrument()  # Uncomment if using Redis
    logger.info("OpenTelemetry instrumentation applied")
except Exception as e:
    logger.warning(f"Could not apply OpenTelemetry instrumentation: {e}")

# Include API router
app.include_router(api_router)

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(content=monitoring_service.get_metrics(), media_type="text/plain")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """
    Initialize the application on startup.
    """
    logger.info("Starting up the recommendation API")
    create_tables()
    logger.info("Database tables created")
    logger.info("Recommendation API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    logger.info("Shutting down the recommendation API")

# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to the Recommendation API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoints (also available via the router, but we'll add them here for convenience)
@app.get("/health")
def health_check():
    """
    Basic health check.
    """
    return {"status": "healthy"}

@app.get("/health/ready")
def readiness_check():
    """
    Readiness check.
    """
    # In a real app, we would check dependencies
    return {"status": "ready"}