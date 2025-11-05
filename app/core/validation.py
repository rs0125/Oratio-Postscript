"""
Enhanced request validation and response serialization utilities.

This module provides comprehensive validation middleware and utilities
for ensuring data integrity and proper serialization.
"""
import json
from typing import Any, Dict, Optional, Union
from datetime import datetime
from decimal import Decimal

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger
from app.core.exceptions import ValidationError as CustomValidationError

logger = get_logger(__name__)


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    Enhanced JSON encoder that handles additional Python types.
    
    This encoder properly serializes datetime objects, Decimal numbers,
    and other common Python types that aren't natively JSON serializable.
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convert non-serializable objects to JSON-serializable format.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'dict') and callable(obj.dict):
            # Handle Pydantic models
            return obj.dict()
        
        return super().default(obj)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for enhanced request validation and preprocessing.
    
    This middleware performs additional validation beyond Pydantic model
    validation, including content-type checking, size limits, and
    custom business rule validation.
    """
    
    def __init__(self, app, max_request_size: int = 26214400):  # 25MB default
        """
        Initialize the validation middleware.
        
        Args:
            app: FastAPI application instance
            max_request_size: Maximum request size in bytes
        """
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with enhanced validation.
        
        Args:
            request: Incoming request
            call_next: Next middleware or endpoint handler
            
        Returns:
            Response from the next handler
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # Validate request size
            content_length = request.headers.get('content-length')
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_request_size:
                    logger.warning(f"Request size {content_length} exceeds limit {self.max_request_size}", extra={
                        "request_id": request_id,
                        "content_length": content_length,
                        "max_size": self.max_request_size
                    })
                    raise CustomValidationError(
                        error_code="REQUEST_TOO_LARGE",
                        message=f"Request size {content_length} bytes exceeds maximum allowed size {self.max_request_size} bytes",
                        details={"content_length": content_length, "max_size": self.max_request_size}
                    )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get('content-type', '').lower()
                if content_type and not any(ct in content_type for ct in ['application/json', 'multipart/form-data']):
                    logger.warning(f"Unsupported content type: {content_type}", extra={
                        "request_id": request_id,
                        "content_type": content_type,
                        "method": request.method
                    })
            
            # Process the request
            response = await call_next(request)
            
            # Enhance response with validation metadata
            if hasattr(request.state, 'validation_passed'):
                response.headers["X-Validation-Status"] = "passed"
            
            return response
            
        except CustomValidationError:
            # Re-raise custom validation errors
            raise
        except Exception as e:
            logger.error(f"Validation middleware error: {e}", extra={
                "request_id": request_id,
                "exception_type": type(e).__name__
            })
            raise


def validate_model_data(model_class: type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    """
    Validate data against a Pydantic model with enhanced error handling.
    
    Args:
        model_class: Pydantic model class to validate against
        data: Data to validate
        
    Returns:
        Validated model instance
        
    Raises:
        CustomValidationError: If validation fails
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        validation_errors = []
        for error in e.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        raise CustomValidationError(
            error_code="MODEL_VALIDATION_ERROR",
            message=f"Validation failed for {model_class.__name__}",
            details={
                "model": model_class.__name__,
                "validation_errors": validation_errors,
                "error_count": len(validation_errors)
            }
        )


def serialize_response(data: Any, exclude_none: bool = True) -> Dict[str, Any]:
    """
    Serialize response data with enhanced handling.
    
    Args:
        data: Data to serialize
        exclude_none: Whether to exclude None values from serialization
        
    Returns:
        Serialized data dictionary
    """
    try:
        if isinstance(data, BaseModel):
            # Use Pydantic's serialization for models
            return data.dict(exclude_none=exclude_none)
        elif hasattr(data, '__dict__'):
            # Handle regular Python objects
            result = {}
            for key, value in data.__dict__.items():
                if exclude_none and value is None:
                    continue
                if isinstance(value, (datetime, Decimal)):
                    result[key] = EnhancedJSONEncoder().default(value)
                else:
                    result[key] = value
            return result
        else:
            # Use FastAPI's jsonable_encoder as fallback
            return jsonable_encoder(data, exclude_none=exclude_none)
    except Exception as e:
        logger.error(f"Response serialization error: {e}")
        # Return a safe fallback
        return {"error": "Serialization failed", "data_type": str(type(data))}


def validate_audio_data(audio_data: str, max_size_mb: int = 25) -> None:
    """
    Validate base64-encoded audio data.
    
    Args:
        audio_data: Base64-encoded audio data
        max_size_mb: Maximum allowed size in MB
        
    Raises:
        CustomValidationError: If validation fails
    """
    import base64
    
    try:
        # Validate base64 format
        decoded_data = base64.b64decode(audio_data, validate=True)
        
        # Check size
        size_mb = len(decoded_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise CustomValidationError(
                error_code="AUDIO_SIZE_EXCEEDED",
                message=f"Audio size {size_mb:.2f}MB exceeds maximum allowed size {max_size_mb}MB",
                details={"size_mb": size_mb, "max_size_mb": max_size_mb}
            )
        
        # Basic audio format validation (check for common audio headers)
        audio_headers = {
            b'RIFF': 'WAV',
            b'ID3': 'MP3',
            b'\xff\xfb': 'MP3',
            b'\xff\xf3': 'MP3',
            b'\xff\xf2': 'MP3',
            b'fLaC': 'FLAC',
            b'OggS': 'OGG'
        }
        
        format_detected = False
        for header, format_name in audio_headers.items():
            if decoded_data.startswith(header):
                format_detected = True
                logger.debug(f"Detected audio format: {format_name}")
                break
        
        if not format_detected:
            logger.warning("Could not detect audio format from headers")
        
    except base64.binascii.Error:
        raise CustomValidationError(
            error_code="INVALID_AUDIO_ENCODING",
            message="Audio data is not valid base64 encoding",
            details={"encoding": "base64"}
        )
    except Exception as e:
        raise CustomValidationError(
            error_code="AUDIO_VALIDATION_ERROR",
            message=f"Audio validation failed: {str(e)}",
            details={"error": str(e)}
        )


def validate_similarity_score(score: float) -> None:
    """
    Validate similarity score is within expected range.
    
    Args:
        score: Similarity score to validate
        
    Raises:
        CustomValidationError: If score is invalid
    """
    if not isinstance(score, (int, float)):
        raise CustomValidationError(
            error_code="INVALID_SIMILARITY_SCORE_TYPE",
            message="Similarity score must be a number",
            details={"score": score, "type": str(type(score))}
        )
    
    if not (0.0 <= score <= 1.0):
        raise CustomValidationError(
            error_code="SIMILARITY_SCORE_OUT_OF_RANGE",
            message="Similarity score must be between 0.0 and 1.0",
            details={"score": score, "min": 0.0, "max": 1.0}
        )