"""
API router for version 1.
"""
from fastapi import APIRouter
from .health import router as health_router
from .recommendations import router as recommendations_router
from .ranking import router as ranking_router
from .events import router as events_router
from .users import router as users_router
from .products import router as products_router
from .experiments import router as experiments_router
from .admin import router as admin_router

router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
router.include_router(ranking_router, prefix="/ranking", tags=["ranking"])
router.include_router(events_router, prefix="/events", tags=["events"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(products_router, prefix="/products", tags=["products"])
router.include_router(experiments_router, prefix="/experiments", tags=["experiments"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])