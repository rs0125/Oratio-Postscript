"""
Global exception handlers for the FastAPI application.

This module provides centralized exception handling to ensure consistent
error responses across all endpoints.
"""

from app.core.logging_config import get_logger
import uuid
from datetime import datetime
from typing import Union

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from app.core.exceptions import (
    SpeechSimilarityAPIError,
    DatabaseError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
    SessionNotFoundError,
    SessionValidationError,
    AudioValidationError,
    AudioProcessingError,
    TranscriptionError,
    ExternalServiceError,
    OpenAIServiceError,
    EmbeddingError,
    WhisperError,
    RateLimitError,
    SimilarityError,
    ValidationError as CustomValidationError,
    ConfigurationError
)

logger = get_logger(__name__)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Unique request identifier
        
    Returns:
        JSONResponse with standardized error format
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
        
    error_response = {
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def speech_similarity_api_exception_handler(
    request: Request, 
    exc: SpeechSimilarityAPIError
) -> JSONResponse:
    """
    Handle custom SpeechSimilarityAPIError exceptions.
    
    This handler processes all custom exceptions that inherit from
    SpeechSimilarityAPIError and maps them to appropriate HTTP status codes.
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Map exception types to HTTP status codes
    status_code_mapping = {
        # Database errors -> 503 Service Unavailable
        DatabaseError: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseTimeoutError: status.HTTP_503_SERVICE_UNAVAILABLE,
        
        # Session errors
        SessionNotFoundError: status.HTTP_404_NOT_FOUND,
        SessionValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        
        # Audio errors
        AudioValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AudioProcessingError: status.HTTP_502_BAD_GATEWAY,
        TranscriptionError: status.HTTP_502_BAD_GATEWAY,
        
        # External service errors -> 502 Bad Gateway
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        OpenAIServiceError: status.HTTP_502_BAD_GATEWAY,
        EmbeddingError: status.HTTP_502_BAD_GATEWAY,
        WhisperError: status.HTTP_502_BAD_GATEWAY,
        
        # Rate limiting -> 429 Too Many Requests
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        
        # Processing errors -> 500 Internal Server Error
        SimilarityError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        
        # Validation errors -> 422 Unprocessable Entity
        CustomValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        
        # Configuration errors -> 500 Internal Server Error
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    # Get status code for this exception type
    status_code = status_code_mapping.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log the error with appropriate level
    if status_code >= 500:
        logger.error(f"Server error ({exc.error_code}): {exc.message}", extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "request_id": request_id,
            "exception_type": type(exc).__name__
        })
    elif status_code >= 400:
        logger.warning(f"Client error ({exc.error_code}): {exc.message}", extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "request_id": request_id,
            "exception_type": type(exc).__name__
        })
    
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=status_code,
        details=exc.details,
        request_id=request_id
    )


async def http_exception_handler(
    request: Request, 
    exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """
    Handle FastAPI HTTPException and Starlette HTTPException.
    
    This handler ensures that HTTP exceptions follow the same
    error response format as custom exceptions.
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Extract error details if they exist
    details = {}
    if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
        # If detail is already a dict (from our custom error responses), use it
        if 'error_code' in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        else:
            details = exc.detail
    elif hasattr(exc, 'detail'):
        details = {"detail": exc.detail}
    
    # Map common HTTP status codes to error codes
    error_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN", 
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_mapping.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if hasattr(exc, 'detail') else f"HTTP {exc.status_code} error"
    
    # Log the error
    if exc.status_code >= 500:
        logger.error(f"HTTP error {exc.status_code}: {message}", extra={
            "status_code": exc.status_code,
            "details": details,
            "request_id": request_id
        })
    elif exc.status_code >= 400:
        logger.warning(f"HTTP error {exc.status_code}: {message}", extra={
            "status_code": exc.status_code,
            "details": details,
            "request_id": request_id
        })
    
    return create_error_response(
        error_code=error_code,
        message=message,
        status_code=exc.status_code,
        details=details,
        request_id=request_id
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors from request parsing.
    
    This handler processes validation errors that occur when
    request data doesn't match the expected Pydantic models.
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    details = {
        "validation_errors": validation_errors,
        "error_count": len(validation_errors)
    }
    
    logger.warning(f"Request validation failed: {len(validation_errors)} errors", extra={
        "validation_errors": validation_errors,
        "request_id": request_id
    })
    
    return create_error_response(
        error_code="REQUEST_VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        request_id=request_id
    )


async def pydantic_validation_exception_handler(
    request: Request, 
    exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic ValidationError exceptions.
    
    This handler processes validation errors that occur during
    data model validation outside of request parsing.
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    details = {
        "validation_errors": validation_errors,
        "error_count": len(validation_errors)
    }
    
    logger.warning(f"Data validation failed: {len(validation_errors)} errors", extra={
        "validation_errors": validation_errors,
        "request_id": request_id
    })
    
    return create_error_response(
        error_code="DATA_VALIDATION_ERROR",
        message="Data validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        request_id=request_id
    )


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Handle any unhandled exceptions.
    
    This is the fallback handler for any exceptions that aren't
    caught by more specific handlers.
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log the unexpected error with full traceback
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", extra={
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "request_id": request_id
    }, exc_info=True)
    
    # Don't expose internal error details in production
    details = {
        "exception_type": type(exc).__name__
    }
    
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id
    )