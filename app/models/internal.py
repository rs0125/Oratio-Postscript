"""Internal models for processing and service layer communication."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class TranscriptionResult(BaseModel):
    """Result from audio transcription service."""
    
    text: str = Field(..., description="Transcribed text from audio")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Transcription confidence score")
    language: Optional[str] = Field(None, description="Detected language code")
    
    @validator('text')
    def validate_text_not_empty(cls, v):
        """Ensure transcribed text is not empty."""
        if not v or not v.strip():
            raise ValueError('Transcribed text cannot be empty')
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "text": "This is the transcribed text from the audio file",
                "confidence": 0.95,
                "language": "en"
            }
        }


class EmbeddingResult(BaseModel):
    """Result from text embedding service."""
    
    vector: List[float] = Field(..., description="Embedding vector representation")
    model: str = Field(..., description="Model used for embedding generation")
    usage_tokens: int = Field(..., ge=0, description="Number of tokens used for embedding")
    
    @validator('vector')
    def validate_vector_not_empty(cls, v):
        """Ensure embedding vector is not empty."""
        if not v or len(v) == 0:
            raise ValueError('Embedding vector cannot be empty')
        return v
    
    @validator('model')
    def validate_model_not_empty(cls, v):
        """Ensure model name is provided."""
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "vector": [0.1, -0.2, 0.3, 0.4, -0.1],
                "model": "text-embedding-ada-002",
                "usage_tokens": 15
            }
        }


class AudioData(BaseModel):
    """Validated audio data for processing."""
    
    base64_content: str = Field(..., description="Base64 encoded audio content")
    format: str = Field(default="wav", description="Audio format")
    channels: int = Field(default=1, ge=1, le=2, description="Number of audio channels")
    
    @validator('base64_content')
    def validate_base64_content(cls, v):
        """Validate base64 content is not empty."""
        if not v or not v.strip():
            raise ValueError('Base64 content cannot be empty')
        return v.strip()
    
    @validator('format')
    def validate_format(cls, v):
        """Validate audio format is supported."""
        supported_formats = ['wav', 'mp3', 'flac', 'm4a']
        if v.lower() not in supported_formats:
            raise ValueError(f'Audio format must be one of: {supported_formats}')
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "base64_content": "UklGRnoGAABXQVZFZm10...",
                "format": "wav",
                "channels": 1
            }
        }


class SimilarityCalculation(BaseModel):
    """Result of similarity calculation between two embeddings."""
    
    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    embedding1_tokens: int = Field(..., ge=0, description="Token count for first embedding")
    embedding2_tokens: int = Field(..., ge=0, description="Token count for second embedding")
    calculation_method: str = Field(default="cosine", description="Method used for similarity calculation")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "score": 0.85,
                "embedding1_tokens": 25,
                "embedding2_tokens": 150,
                "calculation_method": "cosine"
            }
        }