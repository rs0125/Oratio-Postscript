# Speech Similarity API - Endpoint Documentation

## Overview
The Speech Similarity API processes audio data, transcribes it using OpenAI Whisper, and calculates vector similarity between transcribed text and reference documents using OpenAI embeddings.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: None (configure as needed)

**Content-Type**: `application/json`

---

## Endpoints

### 1. Similarity Calculation

#### `POST /similarity/{session_id}`

Calculate similarity between session audio transcription and reference text.

**Description**: This endpoint performs the complete processing pipeline:
1. Retrieves session data from database
2. Decodes and validates audio data  
3. Transcribes audio using OpenAI Whisper
4. Generates embeddings for both transcribed text and reference text
5. Calculates cosine similarity between embeddings

**Parameters**:
- `session_id` (path, integer, required): ID of the session containing audio data

**Request Body**:
```json
{
  "reference_text": "This is a sample reference document that will be used for similarity comparison with the transcribed audio content."
}
```

**Request Schema**:
- `reference_text` (string, required): Reference document text for comparison
  - Min length: 1 character
  - Max length: 50,000 characters
  - Cannot be empty or just whitespace

**Response** (200 OK):
```json
{
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
```

**Response Schema**:
- `session_id`: Session identifier
- `session_data`: Complete session record from database
- `transcribed_text`: Text transcribed from audio using Whisper
- `similarity_score`: Cosine similarity score (0.0-1.0)
- `processing_time_ms`: Total processing time in milliseconds
- `timestamp`: Response generation timestamp

**Error Responses**:
- `404`: Session not found
- `422`: Invalid audio data or request
- `500`: Internal server error
- `502`: External service error (OpenAI API issues)
- `503`: Service unavailable

---

### 2. Session Management

#### `PUT /sessions/{session_id}/audio`

Update audio data for an existing session.

**Description**: Replace the audio data for a session with new base64-encoded audio. Useful for correcting or updating audio recordings without creating new sessions.

**Parameters**:
- `session_id` (path, integer, required): ID of the session to update

**Request Body**:
```json
{
  "audio": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
}
```

**Request Schema**:
- `audio` (string, required): Base64 encoded audio file
  - Supported formats: WAV, MP3, FLAC, M4A, OGG, WebM
  - Must be valid base64 data
  - Minimum size: 44 bytes (WAV header minimum)
  - Maximum size: 25MB (configurable)

**Response** (200 OK):
```json
{
  "session_id": 123,
  "message": "Audio data updated successfully",
  "updated_at": "2023-10-31T10:35:00Z"
}
```

**Error Responses**:
- `404`: Session not found
- `422`: Invalid audio data
- `500`: Internal server error
- `503`: Database service unavailable

---

### 3. Health Monitoring

#### `GET /health`

Comprehensive health check of the service and its dependencies.

**Description**: Checks the health of all critical dependencies including database connection (Supabase) and external service availability.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2023-10-31T10:35:00Z",
  "version": "1.0.0",
  "dependencies": {
    "supabase": "connected",
    "openai": "available"
  }
}
```

**Response Schema**:
- `status`: Service health status ("healthy" or "unhealthy")
- `timestamp`: Health check timestamp
- `version`: API version
- `dependencies`: Status of external dependencies

**Error Responses**:
- `503`: Service is unhealthy

#### `GET /ready`

Readiness check for load balancers and orchestration systems.

**Description**: Determines if the service can handle requests. Used by load balancers to decide if the service should receive traffic.

**Response** (200 OK):
```json
{
  "ready": true,
  "timestamp": "2023-10-31T10:35:00Z",
  "checks": {
    "database": "ready",
    "external_services": "ready"
  }
}
```

**Error Responses**:
- `503`: Service is not ready

---

### 4. Performance Monitoring

#### `GET /monitoring/metrics`

Retrieve comprehensive performance metrics and statistics.

**Parameters**:
- `reset` (query, boolean, optional): Reset metrics after retrieval (default: false)

**Response** (200 OK):
```json
{
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
    },
    "disk": {
      "total_bytes": 1000000000000,
      "free_bytes": 500000000000,
      "used_bytes": 500000000000,
      "usage_percent": 50.0
    },
    "network": {
      "bytes_sent": 1048576,
      "bytes_recv": 2097152,
      "packets_sent": 1000,
      "packets_recv": 1500
    }
  }
}
```

#### `GET /monitoring/system-health`

Retrieve comprehensive system health information including resource usage.

**Response** (200 OK):
```json
{
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
    "memory": {"usage_percent": 50.0, "available_bytes": 4294967296},
    "disk": {"usage_percent": 50.0, "free_bytes": 500000000000},
    "network": {
      "bytes_sent": 1048576,
      "bytes_recv": 2097152
    }
  },
  "performance_summary": {
    "total_requests": 150,
    "error_rate": 6.67,
    "average_response_time": 0.837,
    "requests_per_minute": 2.5
  }
}
```

#### `POST /monitoring/metrics/reset`

Reset all performance metrics to zero.

**Response** (200 OK):
```json
{
  "message": "Performance metrics reset successfully",
  "timestamp": "2023-10-31T10:35:00Z",
  "previous_stats": {
    "total_requests": 150,
    "total_errors": 10
  }
}
```

---

## Error Response Format

All endpoints return errors in a consistent format:

```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session with ID 123 was not found",
  "details": {"session_id": 123, "table": "sessions"},
  "timestamp": "2023-10-31T10:35:00Z",
  "request_id": "req_abc123def456"
}
```

**Error Schema**:
- `error_code`: Machine-readable error code
- `message`: Human-readable error message  
- `details`: Additional error details (optional)
- `timestamp`: Error occurrence timestamp
- `request_id`: Unique request identifier for tracking

---

## Common Error Codes

- `SESSION_NOT_FOUND`: Requested session does not exist
- `SESSION_VALIDATION_ERROR`: Session data validation failed
- `AUDIO_VALIDATION_ERROR`: Audio data format or encoding invalid
- `AUDIO_PROCESSING_ERROR`: Audio processing failed
- `TRANSCRIPTION_ERROR`: Speech-to-text transcription failed
- `EMBEDDING_ERROR`: Text embedding generation failed
- `SIMILARITY_ERROR`: Similarity calculation failed
- `DATABASE_ERROR`: Database operation failed
- `DATABASE_CONNECTION_ERROR`: Database connection failed
- `EXTERNAL_SERVICE_ERROR`: External API (OpenAI) error

---

## Rate Limits & Constraints

- **Max audio size**: 25MB (configurable via `MAX_AUDIO_SIZE_MB`)
- **Request timeout**: 300 seconds (configurable via `REQUEST_TIMEOUT_SECONDS`)
- **Reference text limit**: 50,000 characters
- **Supported audio formats**: WAV, MP3, FLAC, M4A, OGG, WebM
- **Audio encoding**: Base64

---

## Development & Testing

**Start the server**:
```bash
uvicorn app.main:app --reload
```

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

**Environment Setup**:
Copy `.env.example` to `.env` and configure:
- `SUPABASE_URL` and `SUPABASE_KEY`
- `OPENAI_API_KEY`
- Other optional settings

---

## Session Data Structure

Sessions stored in the database contain:

```json
{
  "id": 123,
  "speech": "Optional transcribed speech text",
  "questions": {"q1": "What is the main topic?"},
  "created_by": "user123", 
  "generated_by": "speech-api-v1",
  "created_at": "2023-10-31T10:30:00Z",
  "audio": "base64_encoded_audio_data"
}
```

The `audio` field contains the base64-encoded audio data that gets processed by the similarity endpoint.