"""
Database connection and client configuration for Supabase Session Pooler.
"""
from app.core.logging_config import get_logger
from typing import Optional
import asyncpg
import asyncio
from contextlib import asynccontextmanager

logger = get_logger(__name__)


class DatabaseClient:
    """Supabase session pooler database client with connection pooling."""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._is_connected = False
    
    async def get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await self._create_pool()
        return self._pool
    
    async def _create_pool(self) -> asyncpg.Pool:
        """Create PostgreSQL connection pool using session pooler."""
        try:
            from app.core.config import settings
            
            # Create connection pool with session pooler connection string
            pool = await asyncpg.create_pool(
                dsn=settings.supabase_pooler_connection_string,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance with pooling
                }
            )
            
            logger.info("Supabase session pooler connection pool created successfully")
            self._is_connected = True
            return pool
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            self._is_connected = False
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        pool = await self.get_pool()
        async with pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """Execute a command (INSERT, UPDATE, DELETE)."""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            # Simple query to test connection
            result = await self.execute_query("SELECT 1 as health_check LIMIT 1")
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
    
    async def disconnect(self):
        """Disconnect from database and close pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_connected = False
            logger.info("Database connection pool closed")


# Global database client instance
db_client = DatabaseClient()


def get_database_client() -> DatabaseClient:
    """Dependency injection function for database client."""
    return db_client