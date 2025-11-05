"""
Embedding service for text vectorization using OpenAI embeddings API.
"""
import asyncio
from typing import List, Dict, Any, Optional
from app.core.logging_config import get_logger
from openai import AsyncOpenAI
import numpy as np

from app.core.config import settings
from app.core.exceptions import (
    EmbeddingError,
    ValidationError,
    RateLimitError
)

logger = get_logger(__name__)


class EmbeddingResult:
    """Container for embedding results."""
    
    def __init__(self, vector: List[float], model: str, usage_tokens: int):
        self.vector = vector
        self.model = model
        self.usage_tokens = usage_tokens
        
    def to_numpy(self) -> np.ndarray:
        """Convert vector to numpy array."""
        return np.array(self.vector)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API."""
    
    def __init__(self):
        """Initialize the embedding service with OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        self.model = "text-embedding-ada-002"
        self.max_tokens = 8191  # Max tokens for ada-002 model
        
    async def get_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            EmbeddingResult containing vector and metadata
            
        Raises:
            EmbeddingValidationError: If text is invalid
            EmbeddingAPIError: If OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty", field="text")
            
        # Truncate text if too long (rough estimate: 1 token ≈ 4 characters)
        if len(text) > self.max_tokens * 4:
            text = text[:self.max_tokens * 4]
            logger.warning(f"Text truncated to {self.max_tokens * 4} characters")
            
        try:
            logger.debug(f"Generating embedding for text of length {len(text)}")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding_data = response.data[0]
            usage = response.usage
            
            result = EmbeddingResult(
                vector=embedding_data.embedding,
                model=self.model,
                usage_tokens=usage.total_tokens
            )
            
            logger.debug(f"Generated embedding with {len(result.vector)} dimensions, "
                        f"used {result.usage_tokens} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            # Check for rate limiting
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise RateLimitError("openai", details={"operation": "embedding_generation"})
            raise EmbeddingError(f"OpenAI embeddings API error: {str(e)}", details={"operation": "single_embedding"})
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of EmbeddingResult objects
            
        Raises:
            EmbeddingValidationError: If texts list is invalid
            EmbeddingAPIError: If OpenAI API call fails
        """
        if not texts:
            raise ValidationError("Texts list cannot be empty", field="texts")
            
        # Filter and validate texts
        valid_texts = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                logger.warning(f"Skipping empty text at index {i}")
                continue
                
            # Truncate if necessary
            if len(text) > self.max_tokens * 4:
                text = text[:self.max_tokens * 4]
                logger.warning(f"Text at index {i} truncated to {self.max_tokens * 4} characters")
                
            valid_texts.append(text)
            
        if not valid_texts:
            raise ValidationError("No valid texts found after filtering", field="texts")
            
        try:
            logger.debug(f"Generating embeddings for {len(valid_texts)} texts")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                encoding_format="float"
            )
            
            results = []
            for embedding_data in response.data:
                result = EmbeddingResult(
                    vector=embedding_data.embedding,
                    model=self.model,
                    usage_tokens=response.usage.total_tokens // len(response.data)  # Approximate per-text usage
                )
                results.append(result)
                
            logger.debug(f"Generated {len(results)} embeddings, "
                        f"total tokens used: {response.usage.total_tokens}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            # Check for rate limiting
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise RateLimitError("openai", details={"operation": "batch_embedding_generation"})
            raise EmbeddingError(f"OpenAI embeddings API error: {str(e)}", details={"operation": "batch_embeddings"})
    
    async def close(self):
        """Close the OpenAI client connection."""
        await self.client.close()