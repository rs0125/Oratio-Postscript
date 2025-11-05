"""
Health check service for monitoring database and external service connections.
"""
from app.core.logging_config import get_logger
from typing import Dict, Any
from datetime import datetime
from app.core.database import DatabaseClient

logger = get_logger(__name__)


class HealthService:
    """Service for health checks and monitoring."""
    
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
    
    async def check_database_health(self) -> Dict[str, Any]:
        """
        Check database connection health.
        
        Returns:
            Dictionary with health status and details
        """
        try:
            logger.debug("Performing database health check")
            
            start_time = datetime.utcnow()
            is_healthy = await self.db_client.health_check()
            end_time = datetime.utcnow()
            
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "service": "database",
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": response_time_ms,
                "timestamp": end_time.isoformat(),
                "details": {
                    "provider": "supabase",
                    "connected": self.db_client.is_connected
                }
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "service": "database",
                "status": "unhealthy",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "details": {
                    "provider": "supabase",
                    "connected": False
                }
            }
    
    async def check_overall_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all services.
        
        Returns:
            Dictionary with overall health status
        """
        try:
            logger.info("Performing overall health check")
            
            # Check database
            db_health = await self.check_database_health()
            
            # Determine overall status
            all_healthy = db_health["status"] == "healthy"
            overall_status = "healthy" if all_healthy else "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "database": db_health
                },
                "summary": {
                    "total_services": 1,
                    "healthy_services": 1 if all_healthy else 0,
                    "unhealthy_services": 0 if all_healthy else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Overall health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "services": {},
                "summary": {
                    "total_services": 0,
                    "healthy_services": 0,
                    "unhealthy_services": 1
                }
            }
    
    async def check_readiness(self) -> Dict[str, Any]:
        """
        Check if the service is ready to handle requests.
        
        Returns:
            Dictionary with readiness status
        """
        try:
            logger.debug("Performing readiness check")
            
            # For readiness, we need database to be available
            db_health = await self.check_database_health()
            is_ready = db_health["status"] == "healthy"
            
            return {
                "ready": is_ready,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": db_health["status"]
                }
            }
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return {
                "ready": False,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {
                    "database": "unhealthy"
                }
            }