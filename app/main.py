"""
FastAPI application entry point for Speech Similarity API.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.v1.router import api_router
from app.core.exceptions import SpeechSimilarityAPIError
from app.core.exception_handlers import (
    speech_similarity_api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    generic_exception_handler
)
from app.core.middleware import RequestTrackingMiddleware, SecurityHeadersMiddleware
from app.core.validation import RequestValidationMiddleware
from app.core.openapi import setup_openapi_documentation

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    logger.info("Creating FastAPI application", extra={
        "event": "app_startup",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    })
    
    # Enhanced OpenAPI documentation configuration
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A FastAPI service for calculating similarity between speech transcriptions and reference text using OpenAI embeddings",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        contact={
            "name": "Speech Similarity API Support",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ],
        openapi_tags=[
            {
                "name": "similarity",
                "description": "Speech similarity calculation operations"
            },
            {
                "name": "sessions",
                "description": "Session management operations"
            },
            {
                "name": "health",
                "description": "Health check and monitoring operations"
            },
            {
                "name": "monitoring",
                "description": "System monitoring and metrics operations"
            }
        ]
    )

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestValidationMiddleware, max_request_size=settings.max_audio_size_mb * 1024 * 1024)
    app.add_middleware(RequestTrackingMiddleware)
    
    # Enhanced CORS middleware configuration
    cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-Correlation-ID"
        ],
        expose_headers=[
            "X-Request-ID",
            "X-Correlation-ID",
            "X-Processing-Time",
            "X-API-Version"
        ],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    # Register exception handlers (order matters - most specific first)
    app.add_exception_handler(SpeechSimilarityAPIError, speech_similarity_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Setup enhanced OpenAPI documentation
    setup_openapi_documentation(app)
    
    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup."""
        logger.info("Application startup initiated", extra={
            "event": "app_startup",
            "app_name": settings.app_name,
            "version": settings.app_version
        })
        
        # Initialize database connection
        try:
            from app.core.database import get_database_client
            db_client = get_database_client()
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
        
        logger.info("Application startup completed successfully", extra={
            "event": "app_startup_complete"
        })
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown."""
        logger.info("Application shutdown initiated", extra={
            "event": "app_shutdown"
        })
        
        # Cleanup resources
        try:
            # Add any cleanup logic here
            logger.info("Resource cleanup completed")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
        
        logger.info("Application shutdown completed", extra={
            "event": "app_shutdown_complete"
        })
    
    logger.info("FastAPI application created successfully", extra={
        "event": "app_created"
    })

    return app


app = create_app()