"""
Main API router.
"""
from fastapi import APIRouter
from .v1 import router as v1_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/api/v1")

# Health check endpoints can be added at the root level