"""Database entity models for the Speech Similarity API."""

from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, Field, field_validator


class SessionRecord(BaseModel):
    """Database model for session records stored in Supabase."""
    
    id: int = Field(..., description="Unique session identifier")
    speech: Optional[str] = Field(None, description="Transcribed speech content from audio using Whisper")
    questions: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(None, description="JSONB field containing questions data")
    created_by: Optional[str] = Field(None, description="User who created the session")
    generated_by: Optional[str] = Field(None, description="System or process that generated the session")
    created_at: datetime = Field(..., description="Timestamp when session was created")
    audio: Optional[str] = Field(None, description="Transcribed text content (stored in audio column)")
    original_paper: Optional[str] = Field(None, description="Original paper content")
    
    @field_validator('questions')
    @classmethod
    def validate_questions(cls, v):
        """Accept both dict and list formats for questions field."""
        if v is None:
            return None
        # If it's already a dict, return as-is
        if isinstance(v, dict):
            return v
        # If it's a list, convert to dict with indexed keys
        if isinstance(v, list):
            return {f"q{i+1}": item for i, item in enumerate(v)}
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": 123,
                "speech": "This is the transcribed speech content from the audio file using OpenAI Whisper. The user was discussing the main topic and how it relates to various concepts.",
                "questions": {"q1": "What is the main topic?", "q2": "How does this relate to the reference?"},
                "created_by": "user123",
                "generated_by": "speech-api-v1",
                "created_at": "2023-10-31T10:30:00Z"
            }
        }