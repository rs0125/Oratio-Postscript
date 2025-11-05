"""
Session repository for database operations.
"""
from app.core.logging_config import get_logger
from typing import Optional, List
from datetime import datetime
from supabase import Client
from app.models.database import SessionRecord
from app.core.database import DatabaseClient

logger = get_logger(__name__)


class SessionRepository:
    """Repository for session data access operations."""
    
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
        self.table_name = "sessions"
    
    @property
    def client(self) -> Client:
        """Get Supabase client."""
        return self.db_client.client
    
    async def get_by_id(self, session_id: int) -> Optional[SessionRecord]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            SessionRecord if found, None otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Retrieving session with ID: {session_id}")
            
            result = self.client.table(self.table_name).select("*").eq("id", session_id).execute()
            
            if not result.data:
                logger.info(f"Session not found with ID: {session_id}")
                return None
            
            session_data = result.data[0]
            session_record = SessionRecord(**session_data)
            
            logger.debug(f"Successfully retrieved session: {session_id}")
            return session_record
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            raise
    
    async def update_audio(self, session_id: int, audio_data: str) -> bool:
        """
        Update audio data for an existing session.
        
        Args:
            session_id: The session ID to update
            audio_data: Base64 encoded audio data
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Updating audio for session: {session_id}")
            
            result = self.client.table(self.table_name).update({
                "audio": audio_data
            }).eq("id", session_id).execute()
            
            if not result.data:
                logger.warning(f"No session found to update with ID: {session_id}")
                return False
            
            logger.info(f"Successfully updated audio for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update audio for session {session_id}: {e}")
            raise
    
    async def create(self, session_data: dict) -> SessionRecord:
        """
        Create a new session record.
        
        Args:
            session_data: Dictionary containing session data
            
        Returns:
            Created SessionRecord
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug("Creating new session record")
            
            # Ensure created_at is set
            if "created_at" not in session_data:
                session_data["created_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table(self.table_name).insert(session_data).execute()
            
            if not result.data:
                raise Exception("Failed to create session - no data returned")
            
            created_session = SessionRecord(**result.data[0])
            logger.info(f"Successfully created session with ID: {created_session.id}")
            return created_session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def delete(self, session_id: int) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deletion successful, False if session not found
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Deleting session with ID: {session_id}")
            
            result = self.client.table(self.table_name).delete().eq("id", session_id).execute()
            
            if not result.data:
                logger.warning(f"No session found to delete with ID: {session_id}")
                return False
            
            logger.info(f"Successfully deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[SessionRecord]:
        """
        List sessions with pagination.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of SessionRecord objects
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Listing sessions with limit: {limit}, offset: {offset}")
            
            result = (self.client.table(self.table_name)
                     .select("*")
                     .order("created_at", desc=True)
                     .range(offset, offset + limit - 1)
                     .execute())
            
            sessions = [SessionRecord(**session_data) for session_data in result.data]
            
            logger.debug(f"Retrieved {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise
    
    async def exists(self, session_id: int) -> bool:
        """
        Check if a session exists by ID.
        
        Args:
            session_id: The session ID to check
            
        Returns:
            True if session exists, False otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Checking if session exists: {session_id}")
            
            result = (self.client.table(self.table_name)
                     .select("id")
                     .eq("id", session_id)
                     .limit(1)
                     .execute())
            
            exists = len(result.data) > 0
            logger.debug(f"Session {session_id} exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            raise