# Speech Similarity API

A FastAPI backend service that processes audio data, converts speech to text using OpenAI Whisper, and calculates vector similarity between transcribed text and reference documents.

## Project Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── core/
│   ├── __init__.py
│   └── config.py          # Pydantic settings configuration
├── models/                # Data models and schemas
│   └── __init__.py
├── services/              # Business logic services
│   └── __init__.py
├── repositories/          # Data access layer
│   └── __init__.py
└── api/
    ├── __init__.py
    └── v1/
        ├── __init__.py
        ├── router.py      # Main API router
        └── endpoints/     # API endpoint implementations
            └── __init__.py
```

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration values
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `uvicorn app.main:app --reload`

## Environment Variables

See `.env.example` for all required environment variables.

## API Documentation

When running in debug mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc