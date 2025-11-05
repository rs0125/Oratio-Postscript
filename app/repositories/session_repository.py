"""
Session repository for database operations using Supabase Session Pooler.
"""
from app.core.logging_config import get_logger
from typing import Optional, List
from datetime import datetime
import json
from app.models.database import SessionRecord
from app.core.database import DatabaseClient

logger = get_logger(__name__)


class SessionRepository:
    """Repository for session data access operations using PostgreSQL connection."""
    
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
        self.table_name = "sessions"
    
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
            
            query = f"SELECT * FROM {self.table_name} WHERE id = $1"
            result = await self.db_client.execute_query(query, session_id)
            
            if not result:
                logger.info(f"Session not found with ID: {session_id}")
                return None
            
            # Convert asyncpg Record to dict
            session_data = dict(result[0])
            
            # Handle JSONB fields
            if session_data.get('questions') and isinstance(session_data['questions'], str):
                session_data['questions'] = json.loads(session_data['questions'])
            
            session_record = SessionRecord(**session_data)
            
            logger.debug(f"Successfully retrieved session: {session_id}")
            return session_record
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            raise
    
    async def update_speech(self, session_id: int, speech_text: str) -> bool:
        """
        Update transcribed text for an existing session (stored in audio column).
        
        Args:
            session_id: The session ID to update
            speech_text: Transcribed speech text
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Updating transcribed text for session: {session_id}")
            
            query = f"UPDATE {self.table_name} SET audio = $1 WHERE id = $2"
            result = await self.db_client.execute_command(query, speech_text, session_id)
            
            # Check if any rows were affected
            if result == "UPDATE 0":
                logger.warning(f"No session found to update with ID: {session_id}")
                return False
            
            logger.info(f"Successfully updated transcribed text for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update transcribed text for session {session_id}: {e}")
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
                session_data["created_at"] = datetime.utcnow()
            
            # Handle JSONB fields
            questions_json = json.dumps(session_data.get('questions', {})) if session_data.get('questions') else None
            
            query = f"""
                INSERT INTO {self.table_name} (speech, questions, created_by, generated_by, created_at, audio, original_paper)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            
            result = await self.db_client.execute_query(
                query,
                session_data.get('speech'),
                questions_json,
                session_data.get('created_by'),
                session_data.get('generated_by'),
                session_data['created_at'],
                session_data.get('audio'),
                session_data.get('original_paper')
            )
            
            if not result:
                raise Exception("Failed to create session - no data returned")
            
            # Convert result to dict and handle JSONB
            created_data = dict(result[0])
            if created_data.get('questions') and isinstance(created_data['questions'], str):
                created_data['questions'] = json.loads(created_data['questions'])
            
            created_session = SessionRecord(**created_data)
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
            
            query = f"DELETE FROM {self.table_name} WHERE id = $1"
            result = await self.db_client.execute_command(query, session_id)
            
            if result == "DELETE 0":
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
            
            query = f"""
                SELECT * FROM {self.table_name}
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            result = await self.db_client.execute_query(query, limit, offset)
            
            sessions = []
            for row in result:
                session_data = dict(row)
                # Handle JSONB fields
                if session_data.get('questions') and isinstance(session_data['questions'], str):
                    session_data['questions'] = json.loads(session_data['questions'])
                sessions.append(SessionRecord(**session_data))
            
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
            
            query = f"SELECT 1 FROM {self.table_name} WHERE id = $1 LIMIT 1"
            result = await self.db_client.execute_query(query, session_id)
            
            exists = len(result) > 0
            logger.debug(f"Session {session_id} exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            raise