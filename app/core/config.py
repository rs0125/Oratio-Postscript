"""
Application configuration using Pydantic Settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Speech Similarity API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database - Supabase Session Pooler
    supabase_pooler_connection_string: str = Field(..., env="SUPABASE_POOLER_CONNECTION_STRING")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_organization: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")
    
    # Performance and limits
    max_audio_size_mb: int = Field(default=25, env="MAX_AUDIO_SIZE_MB")
    
    # Security
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # Logging and monitoring
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(default=True, env="STRUCTURED_LOGGING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()