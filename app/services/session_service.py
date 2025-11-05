"""
Session service layer with business logic.
"""
from app.core.logging_config import get_logger
from typing import Optional, List
from datetime import datetime
from app.models.database import SessionRecord
from app.repositories.session_repository import SessionRepository
from app.core.database import DatabaseClient
from app.core.exceptions import (
    SessionNotFoundError,
    SessionValidationError,
    DatabaseError,
    DatabaseConnectionError
)

logger = get_logger(__name__)


class SessionService:
    """Service layer for session business logic."""
    
    def __init__(self, db_client: DatabaseClient):
        self.repository = SessionRepository(db_client)
    
    async def get_session(self, session_id: int) -> SessionRecord:
        """
        Retrieve a session by ID with business logic validation.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SessionRecord
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionValidationError: If session data is invalid
            Exception: For other database errors
        """
        try:
            logger.info(f"Getting session: {session_id}")
            
            if session_id <= 0:
                raise SessionValidationError("Session ID must be a positive integer")
            
            session = await self.repository.get_by_id(session_id)
            
            if session is None:
                raise SessionNotFoundError(session_id)
            
            # Validate session has required audio data
            if not session.audio or not session.audio.strip():
                raise SessionValidationError(f"Session {session_id} has no audio data", {"session_id": session_id})
            
            logger.info(f"Successfully retrieved session: {session_id}")
            return session
            
        except (SessionNotFoundError, SessionValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            # Wrap database errors
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise DatabaseConnectionError(str(e), {"session_id": session_id})
            raise DatabaseError(str(e), {"session_id": session_id})
    
    async def update_session_audio(self, session_id: int, audio_data: str) -> SessionRecord:
        """
        Update audio data for an existing session.
        
        Args:
            session_id: The session ID to update
            audio_data: Base64 encoded audio data
            
        Returns:
            Updated SessionRecord
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionValidationError: If audio data is invalid
            Exception: For other database errors
        """
        try:
            logger.info(f"Updating audio for session: {session_id}")
            
            if session_id <= 0:
                raise SessionValidationError("Session ID must be a positive integer")
            
            if not audio_data or not audio_data.strip():
                raise SessionValidationError("Audio data cannot be empty")
            
            # Validate base64 format (basic check)
            try:
                import base64
                base64.b64decode(audio_data, validate=True)
            except Exception:
                raise SessionValidationError("Invalid base64 audio data format")
            
            # Check if session exists first
            if not await self.repository.exists(session_id):
                raise SessionNotFoundError(session_id)
            
            # Update the audio data
            success = await self.repository.update_audio(session_id, audio_data.strip())
            
            if not success:
                raise DatabaseError("Failed to update session audio", {"session_id": session_id})
            
            # Return updated session
            updated_session = await self.repository.get_by_id(session_id)
            
            logger.info(f"Successfully updated audio for session: {session_id}")
            return updated_session
            
        except (SessionNotFoundError, SessionValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update session audio {session_id}: {e}")
            # Wrap database errors
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise DatabaseConnectionError(str(e), {"session_id": session_id})
            raise DatabaseError(str(e), {"session_id": session_id})
    
    async def create_session(self, session_data: dict) -> SessionRecord:
        """
        Create a new session with validation.
        
        Args:
            session_data: Dictionary containing session data
            
        Returns:
            Created SessionRecord
            
        Raises:
            SessionValidationError: If session data is invalid
            Exception: For database errors
        """
        try:
            logger.info("Creating new session")
            
            # Validate required fields
            if "audio" not in session_data or not session_data["audio"]:
                raise SessionValidationError("Audio data is required for session creation")
            
            # Validate base64 format
            try:
                import base64
                base64.b64decode(session_data["audio"], validate=True)
            except Exception:
                raise SessionValidationError("Invalid base64 audio data format")
            
            # Set default values
            if "created_at" not in session_data:
                session_data["created_at"] = datetime.utcnow()
            
            created_session = await self.repository.create(session_data)
            
            logger.info(f"Successfully created session: {created_session.id}")
            return created_session
            
        except SessionValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def delete_session(self, session_id: int) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionValidationError: If session ID is invalid
            Exception: For other database errors
        """
        try:
            logger.info(f"Deleting session: {session_id}")
            
            if session_id <= 0:
                raise SessionValidationError("Session ID must be a positive integer")
            
            # Check if session exists first
            if not await self.repository.exists(session_id):
                raise SessionNotFoundError(f"Session not found with ID: {session_id}")
            
            success = await self.repository.delete(session_id)
            
            if success:
                logger.info(f"Successfully deleted session: {session_id}")
            
            return success
            
        except (SessionNotFoundError, SessionValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[SessionRecord]:
        """
        List sessions with pagination and validation.
        
        Args:
            limit: Maximum number of sessions to return (1-1000)
            offset: Number of sessions to skip (>= 0)
            
        Returns:
            List of SessionRecord objects
            
        Raises:
            SessionValidationError: If pagination parameters are invalid
            Exception: For database errors
        """
        try:
            logger.info(f"Listing sessions with limit: {limit}, offset: {offset}")
            
            # Validate pagination parameters
            if limit <= 0 or limit > 1000:
                raise SessionValidationError("Limit must be between 1 and 1000")
            
            if offset < 0:
                raise SessionValidationError("Offset must be non-negative")
            
            sessions = await self.repository.list_sessions(limit, offset)
            
            logger.info(f"Successfully retrieved {len(sessions)} sessions")
            return sessions
            
        except SessionValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise
    
    async def session_exists(self, session_id: int) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: The session ID to check
            
        Returns:
            True if session exists, False otherwise
            
        Raises:
            SessionValidationError: If session ID is invalid
            Exception: For database errors
        """
        try:
            if session_id <= 0:
                raise SessionValidationError("Session ID must be a positive integer")
            
            return await self.repository.exists(session_id)
            
        except SessionValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            raise