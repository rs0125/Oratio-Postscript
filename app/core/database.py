"""
Database connection and client configuration for Supabase.
"""
from app.core.logging_config import get_logger
from typing import Optional
from supabase import create_client, Client

logger = get_logger(__name__)


class DatabaseClient:
    """Supabase database client with connection pooling."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._is_connected = False
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client instance."""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self) -> Client:
        """Create Supabase client with configuration."""
        try:
            from app.core.config import settings
            client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_key
            )
            logger.info("Supabase client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            # Simple query to test connection
            result = self.client.table("sessions").select("id").limit(1).execute()
            self._is_connected = True
            logger.debug("Database health check passed")
            return True
        except Exception as e:
            self._is_connected = False
            logger.error(f"Database health check failed: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if database is currently connected."""
        return self._is_connected
    
    def disconnect(self):
        """Disconnect from database."""
        if self._client:
            # Supabase client doesn't have explicit disconnect
            # but we can reset the client instance
            self._client = None
            self._is_connected = False
            logger.info("Database client disconnected")


# Global database client instance
db_client = DatabaseClient()


def get_database_client() -> DatabaseClient:
    """Dependency injection function for database client."""
    return db_client