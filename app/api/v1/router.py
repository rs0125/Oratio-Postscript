"""
Main API router for version 1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import similarity, sessions, health, monitoring

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    similarity.router, 
    prefix="/similarity", 
    tags=["similarity"]
)
api_router.include_router(
    sessions.router, 
    prefix="/sessions", 
    tags=["sessions"]
)
api_router.include_router(
    health.router, 
    tags=["health"]
)
api_router.include_router(
    monitoring.router, 
    prefix="/monitoring", 
    tags=["monitoring"]
)