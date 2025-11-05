"""Database entity models for the Speech Similarity API."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SessionRecord(BaseModel):
    """Database model for session records stored in Supabase."""
    
    id: int = Field(..., description="Unique session identifier")
    speech: Optional[str] = Field(None, description="Speech content text")
    questions: Optional[Dict[str, Any]] = Field(None, description="JSONB field containing questions data")
    created_by: Optional[str] = Field(None, description="User who created the session")
    generated_by: Optional[str] = Field(None, description="System or process that generated the session")
    created_at: datetime = Field(..., description="Timestamp when session was created")
    audio: str = Field(..., description="Base64 encoded WAV mono audio file")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": 123,
                "speech": "Sample transcribed speech text",
                "questions": {"q1": "What is the main topic?", "q2": "How does this relate to the reference?"},
                "created_by": "user123",
                "generated_by": "speech-api-v1",
                "created_at": "2023-10-31T10:30:00Z",
                "audio": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
            }
        }