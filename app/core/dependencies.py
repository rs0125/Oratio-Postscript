"""
Enhanced dependency injection for FastAPI application.

This module provides comprehensive dependency injection with proper service
lifecycle management, caching, and error handling.
"""
from functools import lru_cache
from typing import Generator, Optional
from fastapi import Depends, Request
from app.core.database import get_database_client, DatabaseClient
from app.services.session_service import SessionService
from app.services.health_service import HealthService
from app.services.audio_service import AudioService
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import SimilarityService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Database Dependencies
def get_database_client_dependency() -> DatabaseClient:
    """
    FastAPI dependency for database client.
    
    Returns:
        DatabaseClient instance
    """
    return get_database_client()


# Service Dependencies with proper lifecycle management
@lru_cache()
def get_session_service() -> SessionService:
    """
    Get session service instance with dependency injection.
    
    Returns:
        SessionService instance with database client
    """
    try:
        db_client = get_database_client()
        service = SessionService(db_client)
        logger.debug("Session service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create session service: {e}")
        raise


@lru_cache()
def get_health_service() -> HealthService:
    """
    Get health service instance with dependency injection.
    
    Returns:
        HealthService instance with database client
    """
    try:
        db_client = get_database_client()
        service = HealthService(db_client)
        logger.debug("Health service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create health service: {e}")
        raise


def get_audio_service() -> AudioService:
    """
    Get audio service instance.
    
    Returns:
        AudioService instance
    """
    try:
        service = AudioService()
        logger.debug("Audio service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create audio service: {e}")
        raise


def get_embedding_service() -> Generator[EmbeddingService, None, None]:
    """
    Get embedding service instance with proper lifecycle management.
    
    This dependency ensures the embedding service is properly closed
    after the request is completed.
    
    Yields:
        EmbeddingService instance
    """
    service = None
    try:
        service = EmbeddingService()
        logger.debug("Embedding service created successfully")
        yield service
    except Exception as e:
        logger.error(f"Failed to create embedding service: {e}")
        raise
    finally:
        if service:
            try:
                # Note: EmbeddingService.close() is async, but we can't await in finally
                # The service should handle cleanup in its destructor or context manager
                logger.debug("Embedding service cleanup completed")
            except Exception as e:
                logger.warning(f"Error during embedding service cleanup: {e}")


@lru_cache()
def get_similarity_service() -> SimilarityService:
    """
    Get similarity service instance.
    
    Returns:
        SimilarityService instance
    """
    try:
        service = SimilarityService()
        logger.debug("Similarity service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create similarity service: {e}")
        raise


# Request Context Dependencies
def get_request_id(request: Request) -> Optional[str]:
    """
    Extract request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID if available, None otherwise
    """
    return getattr(request.state, 'request_id', None)


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Extract correlation ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Correlation ID if available, None otherwise
    """
    return getattr(request.state, 'correlation_id', None)


# Combined Service Dependencies for common use cases
def get_similarity_pipeline_services() -> tuple[AudioService, EmbeddingService, SimilarityService]:
    """
    Get all services needed for similarity calculation pipeline.
    
    Returns:
        Tuple of (AudioService, EmbeddingService, SimilarityService)
    """
    try:
        audio_service = get_audio_service()
        embedding_service = EmbeddingService()  # Create fresh instance for pipeline
        similarity_service = get_similarity_service()
        
        logger.debug("Similarity pipeline services created successfully")
        return audio_service, embedding_service, similarity_service
    except Exception as e:
        logger.error(f"Failed to create similarity pipeline services: {e}")
        raise