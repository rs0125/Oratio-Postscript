"""
Session management endpoints.
"""
from app.core.logging_config import get_logger
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.requests import AudioUpdateRequest
from app.models.responses import AudioUpdateResponse, ErrorResponse
from app.services.session_service import SessionService
from app.core.exceptions import SessionNotFoundError, SessionValidationError
from app.core.dependencies import get_session_service, get_request_id

logger = get_logger(__name__)

router = APIRouter()


@router.put(
    "/{session_id}/audio",
    response_model=AudioUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update audio data for an existing session",
    description="Replace the audio data for a session with new base64-encoded audio",
    responses={
        200: {"description": "Audio update successful"},
        404: {"description": "Session not found", "model": ErrorResponse},
        422: {"description": "Invalid audio data", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        503: {"description": "Database service unavailable", "model": ErrorResponse},
    }
)
async def update_session_audio(
    session_id: int,
    request: AudioUpdateRequest,
    session_service: SessionService = Depends(get_session_service),
    request_id: Optional[str] = Depends(get_request_id)
) -> AudioUpdateResponse:
    """
    Update the audio data for an existing session.
    
    This endpoint allows clients to replace or correct audio recordings
    without creating new sessions. The audio data must be base64-encoded
    and in a supported format (WAV, MP3, FLAC, M4A, OGG, WebM).
    
    Args:
        session_id: ID of the session to update
        request: Request containing new base64-encoded audio data
        session_service: Injected session service
        
    Returns:
        AudioUpdateResponse with confirmation and timestamp
        
    Raises:
        HTTPException: Various HTTP errors based on failure type
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    
    logger.info(f"Starting audio update for session {session_id} (request: {request_id})")
    
    # Update session audio
    updated_session = await session_service.update_session_audio(
        session_id, 
        request.audio
    )
    logger.info(f"Successfully updated audio for session {session_id}")
    
    # Create response
    response = AudioUpdateResponse(
        session_id=session_id,
        message="Audio data updated successfully",
        updated_at=datetime.utcnow()
    )
    
    logger.info(f"Audio update completed for session {session_id}")
    return response