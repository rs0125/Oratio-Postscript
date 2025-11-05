"""
OpenAPI documentation configuration and customization.

This module provides enhanced OpenAPI documentation with custom schemas,
examples, and comprehensive API documentation.
"""
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import settings


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Custom OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# Speech Similarity API

A comprehensive FastAPI service for calculating similarity between speech transcriptions and reference text using OpenAI embeddings.

## Features

- **Audio Processing**: Support for multiple audio formats (WAV, MP3, FLAC, M4A, OGG, WebM)
- **Speech Transcription**: Powered by OpenAI Whisper for accurate speech-to-text conversion
- **Semantic Similarity**: Advanced similarity calculation using OpenAI embeddings
- **Session Management**: Persistent session storage with audio data management
- **Health Monitoring**: Comprehensive health checks and system monitoring
- **Structured Logging**: Request tracking with correlation IDs and performance metrics

## Authentication

Currently, this API does not require authentication. All endpoints are publicly accessible.

## Rate Limits

- Maximum audio file size: 25MB
- Request timeout: 5 minutes
- Concurrent requests: Limited by server capacity

## Error Handling

All endpoints return standardized error responses with:
- Error codes for programmatic handling
- Human-readable messages
- Detailed error information
- Request tracking IDs
- Timestamps

## Data Privacy

- Audio data is processed in memory and not permanently stored
- Session data includes metadata but not raw audio content
- All processing is performed server-side with secure external API calls
        """,
        routes=app.routes,
    )
    
    # Add custom components
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error_code": {
                    "type": "string",
                    "description": "Machine-readable error code",
                    "example": "SESSION_NOT_FOUND"
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error message",
                    "example": "Session with ID 123 not found"
                },
                "details": {
                    "type": "object",
                    "description": "Additional error details",
                    "example": {"session_id": 123}
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Error timestamp in ISO format",
                    "example": "2023-12-01T10:30:00Z"
                },
                "request_id": {
                    "type": "string",
                    "description": "Unique request identifier for tracking",
                    "example": "req_123e4567-e89b-12d3-a456-426614174000"
                }
            },
            "required": ["error_code", "message", "timestamp", "request_id"]
        }
    })
    
    # Add security schemes (even though not currently used)
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication (not currently implemented)"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT bearer token authentication (not currently implemented)"
        }
    }
    
    # Add custom headers
    openapi_schema["components"]["parameters"] = {
        "RequestId": {
            "name": "X-Request-ID",
            "in": "header",
            "description": "Optional request ID for tracking",
            "required": False,
            "schema": {
                "type": "string",
                "format": "uuid"
            }
        },
        "CorrelationId": {
            "name": "X-Correlation-ID", 
            "in": "header",
            "description": "Optional correlation ID for distributed tracing",
            "required": False,
            "schema": {
                "type": "string",
                "format": "uuid"
            }
        }
    }
    
    # Add response headers
    openapi_schema["components"]["headers"] = {
        "X-Request-ID": {
            "description": "Unique request identifier",
            "schema": {
                "type": "string",
                "format": "uuid"
            }
        },
        "X-Correlation-ID": {
            "description": "Correlation ID for request tracking",
            "schema": {
                "type": "string", 
                "format": "uuid"
            }
        },
        "X-Processing-Time": {
            "description": "Request processing time in seconds",
            "schema": {
                "type": "string",
                "pattern": "^\\d+\\.\\d{3}s$"
            }
        },
        "X-API-Version": {
            "description": "API version",
            "schema": {
                "type": "string"
            }
        }
    }
    
    # Add examples for common responses
    openapi_schema["components"]["examples"] = {
        "SessionNotFoundError": {
            "summary": "Session not found",
            "value": {
                "error_code": "SESSION_NOT_FOUND",
                "message": "Session with ID 123 not found",
                "details": {"session_id": 123},
                "timestamp": "2023-12-01T10:30:00Z",
                "request_id": "req_123e4567-e89b-12d3-a456-426614174000"
            }
        },
        "ValidationError": {
            "summary": "Request validation error",
            "value": {
                "error_code": "REQUEST_VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": [
                        {
                            "field": "audio",
                            "message": "field required",
                            "type": "value_error.missing"
                        }
                    ],
                    "error_count": 1
                },
                "timestamp": "2023-12-01T10:30:00Z",
                "request_id": "req_123e4567-e89b-12d3-a456-426614174000"
            }
        },
        "InternalServerError": {
            "summary": "Internal server error",
            "value": {
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"exception_type": "ValueError"},
                "timestamp": "2023-12-01T10:30:00Z",
                "request_id": "req_123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.example.com",
            "description": "Production server"
        }
    ]
    
    # Add contact and license information
    openapi_schema["info"]["contact"] = {
        "name": "Speech Similarity API Support",
        "email": "support@example.com",
        "url": "https://example.com/support"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "Find more info here",
        "url": "https://example.com/docs"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi_documentation(app: FastAPI) -> None:
    """
    Set up enhanced OpenAPI documentation for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.openapi = lambda: custom_openapi_schema(app)


# Common response examples for reuse across endpoints
COMMON_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error_code": "BAD_REQUEST",
                    "message": "Invalid request format",
                    "details": {},
                    "timestamp": "2023-12-01T10:30:00Z",
                    "request_id": "req_123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "examples": {
                    "validation_error": {"$ref": "#/components/examples/ValidationError"}
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "examples": {
                    "internal_error": {"$ref": "#/components/examples/InternalServerError"}
                }
            }
        }
    },
    503: {
        "description": "Service Unavailable",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "error_code": "SERVICE_UNAVAILABLE",
                    "message": "Database service is temporarily unavailable",
                    "details": {"service": "database"},
                    "timestamp": "2023-12-01T10:30:00Z",
                    "request_id": "req_123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }
    }
}