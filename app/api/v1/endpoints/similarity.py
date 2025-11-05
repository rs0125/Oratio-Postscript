"""
Similarity calculation endpoints.
"""
from app.core.logging_config import get_logger
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.requests import SimilarityRequest
from app.models.responses import SimilarityResponse, ErrorResponse
from app.services.session_service import SessionService
from app.services.audio_service import AudioService
from app.services.embedding_service import EmbeddingService
from app.services.similarity_service import SimilarityService
from app.core.exceptions import (
    SessionNotFoundError,
    SessionValidationError,
    AudioValidationError,
    AudioProcessingError,
    TranscriptionError,
    EmbeddingError,
    SimilarityError,
    DatabaseError,
    DatabaseConnectionError
)
from app.core.dependencies import get_session_service, get_embedding_service, get_request_id

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/{session_id}",
    response_model=SimilarityResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate similarity between session audio and reference text",
    description="Process audio from a session, transcribe it, and calculate similarity with reference document",
    responses={
        200: {"description": "Similarity calculation successful"},
        404: {"description": "Session not found", "model": ErrorResponse},
        422: {"description": "Invalid audio data or request", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        502: {"description": "External service error", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def calculate_similarity(
    session_id: int,
    request: SimilarityRequest,
    session_service: SessionService = Depends(get_session_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    request_id: Optional[str] = Depends(get_request_id)
) -> SimilarityResponse:
    """
    Calculate similarity between session audio transcription and reference text.
    
    This endpoint performs the complete processing pipeline:
    1. Retrieves session data from database
    2. Decodes and validates audio data
    3. Transcribes audio using OpenAI Whisper
    4. Generates embeddings for both transcribed text and reference text
    5. Calculates cosine similarity between embeddings
    
    Args:
        session_id: ID of the session containing audio data
        request: Request containing reference text for comparison
        session_service: Injected session service
        
    Returns:
        SimilarityResponse with session data, transcription, and similarity score
        
    Raises:
        HTTPException: Various HTTP errors based on failure type
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    logger.info(f"Starting similarity calculation for session {session_id} (request: {request_id})")
    
    # Step 1: Retrieve session data
    session_record = await session_service.get_session(session_id)
    logger.info(f"Retrieved session {session_id} successfully")
    
    # Step 2: Process and transcribe audio
    audio_service = AudioService()
    transcription_result = await audio_service.process_and_transcribe(session_record.audio)
    transcribed_text = transcription_result.text
    logger.info(f"Audio transcription completed for session {session_id}")
    
    # Step 3: Generate embeddings using injected service
    try:
        # Generate embeddings for both texts in batch for efficiency
        embedding_results = await embedding_service.get_embeddings_batch([
            transcribed_text,
            request.reference_text
        ])
        
        transcribed_embedding = embedding_results[0]
        reference_embedding = embedding_results[1]
        
        logger.info(f"Generated embeddings for session {session_id}")
    except Exception as e:
        logger.error(f"Embedding generation failed for session {session_id}: {e}")
        raise
    
    # Step 4: Calculate similarity
    similarity_service = SimilarityService()
    similarity_result = similarity_service.calculate_similarity(
        transcribed_embedding.vector,
        reference_embedding.vector
    )
    similarity_score = similarity_result.normalized_score
    logger.info(f"Calculated similarity score {similarity_score:.4f} for session {session_id}")
    
    # Calculate processing time
    end_time = datetime.utcnow()
    processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Create response
    response = SimilarityResponse(
        session_id=session_id,
        session_data=session_record,
        transcribed_text=transcribed_text,
        similarity_score=similarity_score,
        processing_time_ms=processing_time_ms,
        timestamp=end_time
    )
    
    logger.info(f"Similarity calculation completed for session {session_id} in {processing_time_ms}ms")
    return response