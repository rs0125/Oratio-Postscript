"""
Health check endpoints.
"""
from app.core.logging_config import get_logger
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.responses import HealthResponse
from app.services.health_service import HealthService
from app.core.dependencies import get_health_service
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health status of the service and its dependencies",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    }
)
async def health_check(
    health_service: HealthService = Depends(get_health_service)
) -> HealthResponse:
    """
    Perform a comprehensive health check of the service.
    
    This endpoint checks the health of all critical dependencies including:
    - Database connection (Supabase)
    - External service availability
    
    Returns:
        HealthResponse with detailed health information
        
    Raises:
        HTTPException: 503 if service is unhealthy
    """
    try:
        logger.debug("Performing health check")
        
        # Get comprehensive health status
        health_data = await health_service.check_overall_health()
        
        # Determine HTTP status based on health
        http_status = (
            status.HTTP_200_OK 
            if health_data["status"] == "healthy" 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        # Create response
        response = HealthResponse(
            status=health_data["status"],
            timestamp=datetime.fromisoformat(health_data["timestamp"].replace('Z', '+00:00')),
            version=settings.app_version,
            dependencies={
                service_name: service_data["status"]
                for service_name, service_data in health_data["services"].items()
            }
        )
        
        if http_status != status.HTTP_200_OK:
            logger.warning(f"Health check failed: {health_data}")
            raise HTTPException(
                status_code=http_status,
                detail=response.dict()
            )
        
        logger.debug("Health check passed")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.app_version,
                "dependencies": {},
                "error": str(e)
            }
        )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check endpoint",
    description="Check if the service is ready to handle requests",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    }
)
async def readiness_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Perform a readiness check to determine if the service can handle requests.
    
    This is typically used by load balancers and orchestration systems
    to determine if the service should receive traffic.
    
    Returns:
        Simple JSON response indicating readiness status
        
    Raises:
        HTTPException: 503 if service is not ready
    """
    try:
        logger.debug("Performing readiness check")
        
        # Get readiness status
        readiness_data = await health_service.check_readiness()
        
        if not readiness_data["ready"]:
            logger.warning(f"Readiness check failed: {readiness_data}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=readiness_data
            )
        
        logger.debug("Readiness check passed")
        return readiness_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ready": False,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {}
            }
        )