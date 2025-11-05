"""
Custom exception classes for the Speech Similarity API.

This module defines a hierarchy of custom exceptions that provide
structured error handling throughout the application.
"""

from typing import Optional, Dict, Any


class SpeechSimilarityAPIError(Exception):
    """
    Base exception class for all Speech Similarity API errors.
    
    All custom exceptions should inherit from this base class to ensure
    consistent error handling and response formatting.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


# Database-related exceptions
class DatabaseError(SpeechSimilarityAPIError):
    """Base exception for database-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details
        )
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operation times out."""
    
    def __init__(self, message: str = "Database operation timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details
        )
        self.error_code = "DATABASE_TIMEOUT_ERROR"


# Session-related exceptions
class SessionError(SpeechSimilarityAPIError):
    """Base exception for session-related errors."""
    
    def __init__(self, message: str, error_code: str = "SESSION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""
    
    def __init__(self, session_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"Session with ID {session_id} was not found"
        session_details = {"session_id": session_id}
        if details:
            session_details.update(details)
        
        super().__init__(
            message=message,
            error_code="SESSION_NOT_FOUND",
            details=session_details
        )


class SessionValidationError(SessionError):
    """Raised when session data validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SESSION_VALIDATION_ERROR",
            details=details
        )


# Audio processing exceptions
class AudioError(SpeechSimilarityAPIError):
    """Base exception for audio-related errors."""
    
    def __init__(self, message: str, error_code: str = "AUDIO_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class AudioValidationError(AudioError):
    """Raised when audio validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_AUDIO_DATA",
            details=details
        )


class AudioProcessingError(AudioError):
    """Raised when audio processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUDIO_PROCESSING_ERROR",
            details=details
        )


class TranscriptionError(AudioError):
    """Raised when transcription fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TRANSCRIPTION_SERVICE_ERROR",
            details=details
        )


# External service exceptions
class ExternalServiceError(SpeechSimilarityAPIError):
    """Base exception for external service errors."""
    
    def __init__(self, message: str, service_name: str, error_code: str = "EXTERNAL_SERVICE_ERROR", details: Optional[Dict[str, Any]] = None):
        service_details = {"service": service_name}
        if details:
            service_details.update(details)
            
        super().__init__(
            message=message,
            error_code=error_code,
            details=service_details
        )


class OpenAIServiceError(ExternalServiceError):
    """Raised when OpenAI service calls fail."""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        operation_details = {"operation": operation}
        if details:
            operation_details.update(details)
            
        super().__init__(
            message=message,
            service_name="openai",
            error_code="OPENAI_SERVICE_ERROR",
            details=operation_details
        )


class EmbeddingError(OpenAIServiceError):
    """Raised when embedding generation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            operation="embedding_generation",
            details=details
        )
        self.error_code = "EMBEDDING_SERVICE_ERROR"


class WhisperError(OpenAIServiceError):
    """Raised when Whisper transcription fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            operation="speech_transcription",
            details=details
        )
        self.error_code = "WHISPER_SERVICE_ERROR"


# Rate limiting exceptions
class RateLimitError(ExternalServiceError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, service_name: str, retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Rate limit exceeded for {service_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
            
        rate_limit_details = {"retry_after": retry_after}
        if details:
            rate_limit_details.update(details)
            
        super().__init__(
            message=message,
            service_name=service_name,
            error_code="RATE_LIMIT_EXCEEDED",
            details=rate_limit_details
        )


# Processing exceptions
class ProcessingError(SpeechSimilarityAPIError):
    """Base exception for processing-related errors."""
    
    def __init__(self, message: str, error_code: str = "PROCESSING_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class SimilarityError(ProcessingError):
    """Raised when similarity calculation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SIMILARITY_CALCULATION_ERROR",
            details=details
        )


# Validation exceptions
class ValidationError(SpeechSimilarityAPIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        validation_details = {}
        if field:
            validation_details["field"] = field
        if details:
            validation_details.update(details)
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=validation_details
        )


# Configuration exceptions
class ConfigurationError(SpeechSimilarityAPIError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        config_details = {}
        if config_key:
            config_details["config_key"] = config_key
        if details:
            config_details.update(details)
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=config_details
        )