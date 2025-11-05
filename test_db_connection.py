#!/usr/bin/env python3
"""
Test database connection script.
"""
import asyncio
import asyncpg
from app.core.config import settings

async def test_connection():
    try:
        print('Testing connection to:', settings.supabase_pooler_connection_string[:50] + '...')
        conn = await asyncpg.connect(settings.supabase_pooler_connection_string)
        result = await conn.fetchval('SELECT 1')
        print('Connection successful! Result:', result)
        await conn.close()
        return True
    except Exception as e:
        print('Connection failed:', str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("✅ Database connection is working")
    else:
        print("❌ Database connection failed")