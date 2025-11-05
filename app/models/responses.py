"""Response models for API endpoints."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .database import SessionRecord


class SimilarityResponse(BaseModel):
    """Response model for similarity calculation endpoint."""
    
    session_id: int = Field(..., description="Session identifier")
    session_data: SessionRecord = Field(..., description="Complete session record from database")
    transcribed_text: str = Field(..., description="Text transcribed from audio using Whisper")
    similarity_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Cosine similarity score between transcribed text and reference document"
    )
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    timestamp: datetime = Field(..., description="Response generation timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "session_id": 123,
                "session_data": {
                    "id": 123,
                    "speech": "Sample transcribed speech text",
                    "questions": {"q1": "What is the main topic?"},
                    "created_by": "user123",
                    "generated_by": "speech-api-v1",
                    "created_at": "2023-10-31T10:30:00Z",
                    "audio": "UklGRnoGAABXQVZFZm10..."
                },
                "transcribed_text": "This is the transcribed text from the audio file using OpenAI Whisper",
                "similarity_score": 0.85,
                "processing_time_ms": 2500,
                "timestamp": "2023-10-31T10:35:00Z"
            }
        }


class AudioUpdateResponse(BaseModel):
    """Response model for audio update endpoint."""
    
    session_id: int = Field(..., description="Session identifier that was updated")
    message: str = Field(..., description="Success message")
    updated_at: datetime = Field(..., description="Timestamp when update occurred")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "session_id": 123,
                "message": "Audio data updated successfully",
                "updated_at": "2023-10-31T10:35:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")
    request_id: str = Field(..., description="Unique request identifier for tracking")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "error_code": "SESSION_NOT_FOUND",
                "message": "Session with ID 123 was not found",
                "details": {"session_id": 123, "table": "sessions"},
                "timestamp": "2023-10-31T10:35:00Z",
                "request_id": "req_abc123def456"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    dependencies: Dict[str, str] = Field(..., description="Status of external dependencies")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-10-31T10:35:00Z",
                "version": "1.0.0",
                "dependencies": {
                    "supabase": "connected",
                    "openai": "available"
                }
            }
        }


class MetricsResponse(BaseModel):
    """Performance metrics response model."""
    
    timestamp: datetime = Field(..., description="Metrics collection timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    requests: Dict[str, Any] = Field(..., description="Request statistics")
    response_times: Dict[str, Any] = Field(..., description="Response time statistics")
    errors: Dict[str, Any] = Field(..., description="Error statistics")
    system: Dict[str, Any] = Field(..., description="System resource metrics")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "timestamp": "2023-10-31T10:35:00Z",
                "uptime_seconds": 3600.5,
                "requests": {
                    "total": 150,
                    "by_method": {"GET": 100, "POST": 50},
                    "by_status": {"200": 140, "404": 8, "500": 2},
                    "by_endpoint": {"/api/v1/similarity/123": 45, "/api/v1/health": 100}
                },
                "response_times": {
                    "total_time": 125.5,
                    "count": 150,
                    "average": 0.837,
                    "min": 0.001,
                    "max": 5.234
                },
                "errors": {
                    "total": 10,
                    "by_type": {"ValidationError": 8, "DatabaseError": 2}
                },
                "system": {
                    "cpu": {"usage_percent": 15.2, "count": 4},
                    "memory": {
                        "total_bytes": 8589934592,
                        "available_bytes": 4294967296,
                        "used_bytes": 4294967296,
                        "usage_percent": 50.0
                    }
                }
            }
        }


class SystemHealthResponse(BaseModel):
    """Comprehensive system health response model."""
    
    timestamp: datetime = Field(..., description="Health check timestamp")
    status: str = Field(..., description="Overall system health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    dependencies: Dict[str, Any] = Field(..., description="Status of external dependencies")
    system_resources: Dict[str, Any] = Field(..., description="System resource usage")
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary metrics")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "timestamp": "2023-10-31T10:35:00Z",
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "dependencies": {
                    "supabase": {
                        "status": "connected",
                        "response_time": 0.045,
                        "last_check": "2023-10-31T10:35:00Z"
                    },
                    "openai": {
                        "status": "available",
                        "response_time": 0.123,
                        "last_check": "2023-10-31T10:35:00Z"
                    }
                },
                "system_resources": {
                    "cpu": {"usage_percent": 15.2, "count": 4},
                    "memory": {"usage_percent": 50.0, "available_bytes": 4294967296}
                },
                "performance_summary": {
                    "total_requests": 150,
                    "error_rate": 6.67,
                    "average_response_time": 0.837,
                    "requests_per_minute": 2.5
                }
            }
        }