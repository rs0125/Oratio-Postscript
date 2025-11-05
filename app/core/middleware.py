"""
Middleware for the FastAPI application.

This module provides middleware components for request processing,
logging, and error tracking with structured logging and performance metrics.
"""

import uuid
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import (
    get_logger, 
    set_correlation_id, 
    get_correlation_id,
    performance_metrics
)

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for request tracking, structured logging, and performance metrics.
    
    This middleware:
    - Adds a unique request ID and correlation ID to each request
    - Implements structured logging with correlation IDs
    - Tracks detailed performance metrics
    - Logs comprehensive request/response information
    - Adds tracking headers to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with enhanced tracking and logging.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response with added tracking headers and metrics
        """
        # Generate unique request ID and correlation ID
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context
        set_correlation_id(correlation_id)
        
        # Store IDs in request state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Record start time
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        content_length = request.headers.get("content-length")
        
        # Log request start with structured data
        logger.info("Request started", extra={
            "event": "request_started",
            "request_id": request_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_length": content_length,
            "headers": dict(request.headers) if logger.isEnabledFor(10) else None  # DEBUG level
        })
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Add tracking headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            # Record metrics
            performance_metrics.record_request(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                processing_time=processing_time
            )
            
            # Log request completion with structured data
            logger.info("Request completed", extra={
                "event": "request_completed",
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "processing_time": processing_time,
                "response_size": response.headers.get("content-length"),
                "cache_status": response.headers.get("x-cache-status")
            })
            
            return response
            
        except Exception as exc:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            exception_type = type(exc).__name__
            exception_message = str(exc)
            
            # Record error metrics
            performance_metrics.record_error(exception_type)
            
            # Log request failure with structured data
            logger.error("Request failed", extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": method,
                "path": path,
                "processing_time": processing_time,
                "exception_type": exception_type,
                "exception_message": exception_message
            }, exc_info=True)
            
            # Re-raise the exception to be handled by exception handlers
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    
    This middleware adds common security headers to all responses
    to improve the security posture of the API.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to the response.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response with added security headers
        """
        response = await call_next(request)
        
        # Add comprehensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add API-specific headers
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Powered-By"] = "FastAPI"
        
        # Add cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response