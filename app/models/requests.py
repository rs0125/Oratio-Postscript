"""Request models for API endpoints."""

import base64
import re
from typing import Optional
from pydantic import BaseModel, Field, validator


class SimilarityRequest(BaseModel):
    """Request model for similarity calculation endpoint."""
    
    reference_text: str = Field(
        ..., 
        description="Reference document text for comparison",
        min_length=1,
        max_length=50000
    )
    
    @validator('reference_text')
    def validate_reference_text(cls, v):
        """Validate reference text is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Reference text cannot be empty or just whitespace')
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "reference_text": "This is a sample reference document that will be used for similarity comparison with the transcribed audio content."
            }
        }


class AudioUpdateRequest(BaseModel):
    """Request model for updating audio data in a session."""
    
    audio: str = Field(
        ..., 
        description="Base64 encoded WAV mono audio file",
        min_length=1
    )
    
    @validator('audio')
    def validate_audio_base64(cls, v):
        """Validate that audio is valid base64 encoded data."""
        if not v or not v.strip():
            raise ValueError('Audio data cannot be empty')
        
        # Remove any whitespace
        v = v.strip()
        
        # Check if it's valid base64
        try:
            # Add padding if needed
            missing_padding = len(v) % 4
            if missing_padding:
                v += '=' * (4 - missing_padding)
            
            decoded = base64.b64decode(v, validate=True)
            
            # Basic validation - should be at least a few bytes
            if len(decoded) < 44:  # Minimum WAV header size
                raise ValueError('Audio data appears to be too small to be a valid WAV file')
                
        except Exception as e:
            raise ValueError(f'Invalid base64 audio data: {str(e)}')
        
        # Return the properly padded version
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "audio": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
            }
        }