"""
Monitoring and metrics endpoints.

This module provides endpoints for:
- Performance metrics
- System health monitoring
- Application statistics
- Operational insights
"""

import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.core.logging_config import performance_metrics, get_logger
from app.core.config import settings
from app.models.responses import MetricsResponse, SystemHealthResponse
from app.services.health_service import HealthService
from app.core.dependencies import get_health_service

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get performance metrics",
    description="Retrieve comprehensive performance metrics and statistics",
    responses={
        200: {"description": "Performance metrics retrieved successfully"},
        500: {"description": "Internal server error"},
    }
)
async def get_metrics(
    reset: bool = Query(False, description="Reset metrics after retrieval")
) -> MetricsResponse:
    """
    Get comprehensive performance metrics.
    
    Args:
        reset: Whether to reset metrics after retrieval
        
    Returns:
        MetricsResponse with detailed performance data
    """
    try:
        logger.debug("Retrieving performance metrics", extra={
            "event": "metrics_requested",
            "reset_requested": reset
        })
        
        # Get current metrics
        metrics_data = performance_metrics.get_metrics()
        
        # Add system metrics
        system_metrics = _get_system_metrics()
        
        # Create response
        response = MetricsResponse(
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - _get_start_time(),
            requests=metrics_data["requests"],
            response_times=metrics_data["response_times"],
            errors=metrics_data["errors"],
            system=system_metrics
        )
        
        # Reset metrics if requested
        if reset:
            performance_metrics.reset_metrics()
            logger.info("Performance metrics reset", extra={
                "event": "metrics_reset"
            })
        
        logger.debug("Performance metrics retrieved successfully")
        return response
        
    except Exception as e:
        logger.error("Failed to retrieve metrics", extra={
            "event": "metrics_error",
            "error": str(e)
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get(
    "/system-health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed system health",
    description="Retrieve comprehensive system health information including resource usage",
    responses={
        200: {"description": "System health retrieved successfully"},
        500: {"description": "Internal server error"},
    }
)
async def get_system_health(
    health_service: HealthService = Depends(get_health_service)
) -> SystemHealthResponse:
    """
    Get detailed system health information.
    
    Returns:
        SystemHealthResponse with comprehensive health data
    """
    try:
        logger.debug("Retrieving system health information", extra={
            "event": "system_health_requested"
        })
        
        # Get service health
        health_data = await health_service.check_overall_health()
        
        # Get system metrics
        system_metrics = _get_system_metrics()
        
        # Get application metrics
        app_metrics = performance_metrics.get_metrics()
        
        # Create response
        response = SystemHealthResponse(
            timestamp=datetime.utcnow(),
            status=health_data["status"],
            version=settings.app_version,
            uptime_seconds=time.time() - _get_start_time(),
            dependencies=health_data["services"],
            system_resources=system_metrics,
            performance_summary={
                "total_requests": app_metrics["requests"]["total"],
                "error_rate": (
                    app_metrics["errors"]["total"] / max(app_metrics["requests"]["total"], 1)
                ) * 100,
                "average_response_time": app_metrics["response_times"]["average"],
                "requests_per_minute": _calculate_requests_per_minute(app_metrics)
            }
        )
        
        logger.debug("System health retrieved successfully")
        return response
        
    except Exception as e:
        logger.error("Failed to retrieve system health", extra={
            "event": "system_health_error",
            "error": str(e)
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system health: {str(e)}"
        )


@router.post(
    "/metrics/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset performance metrics",
    description="Reset all performance metrics to zero",
    responses={
        200: {"description": "Metrics reset successfully"},
        500: {"description": "Internal server error"},
    }
)
async def reset_metrics() -> JSONResponse:
    """
    Reset all performance metrics.
    
    Returns:
        Confirmation message
    """
    try:
        logger.info("Resetting performance metrics", extra={
            "event": "metrics_reset_requested"
        })
        
        # Get current metrics for logging
        current_metrics = performance_metrics.get_metrics()
        
        # Reset metrics
        performance_metrics.reset_metrics()
        
        logger.info("Performance metrics reset successfully", extra={
            "event": "metrics_reset_completed",
            "previous_total_requests": current_metrics["requests"]["total"],
            "previous_total_errors": current_metrics["errors"]["total"]
        })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Performance metrics reset successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "previous_stats": {
                    "total_requests": current_metrics["requests"]["total"],
                    "total_errors": current_metrics["errors"]["total"]
                }
            }
        )
        
    except Exception as e:
        logger.error("Failed to reset metrics", extra={
            "event": "metrics_reset_error",
            "error": str(e)
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}"
        )


def _get_system_metrics() -> Dict[str, Any]:
    """
    Get current system resource metrics.
    
    Returns:
        Dictionary with system metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics (if available)
        try:
            network = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        except Exception:
            network_stats = None
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "usage_percent": memory.percent
            },
            "disk": {
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "used_bytes": disk.used,
                "usage_percent": (disk.used / disk.total) * 100
            },
            "network": network_stats
        }
        
    except Exception as e:
        logger.warning("Failed to get system metrics", extra={
            "error": str(e)
        })
        return {}


def _get_start_time() -> float:
    """
    Get application start time.
    
    Returns:
        Start time as timestamp
    """
    # This is a simple implementation - in production you might want to
    # store this in a more persistent way
    if not hasattr(_get_start_time, '_start_time'):
        _get_start_time._start_time = time.time()
    return _get_start_time._start_time


def _calculate_requests_per_minute(metrics: Dict[str, Any]) -> float:
    """
    Calculate requests per minute based on current metrics.
    
    Args:
        metrics: Current performance metrics
        
    Returns:
        Requests per minute
    """
    uptime_minutes = (time.time() - _get_start_time()) / 60
    if uptime_minutes > 0:
        return metrics["requests"]["total"] / uptime_minutes
    return 0.0