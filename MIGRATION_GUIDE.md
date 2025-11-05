# Migration Guide: Supabase Session Pooler

This guide explains how to migrate from the standard Supabase client to using Supabase Session Pooler with direct PostgreSQL connections.

## What Changed

### Before (Standard Supabase Client)
- Used `supabase-py` client library
- Connected via REST API
- Configuration: `SUPABASE_URL` + `SUPABASE_KEY`

### After (Session Pooler)
- Uses `asyncpg` for direct PostgreSQL connections
- Connects via Supabase Session Pooler
- Configuration: `SUPABASE_POOLER_CONNECTION_STRING`

## Benefits of Session Pooler

1. **Better Performance**: Direct PostgreSQL connections are faster than REST API calls
2. **Connection Pooling**: Efficient connection reuse and management
3. **Lower Latency**: Eliminates HTTP overhead for database operations
4. **Better Scalability**: Handles high-concurrency workloads more efficiently

## Configuration Changes

### Environment Variables

**Old Configuration:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

**New Configuration:**
```env
SUPABASE_POOLER_CONNECTION_STRING=postgresql://postgres.your-project:password@aws-0-region.pooler.supabase.com:6543/postgres
```

### Getting Your Session Pooler Connection String

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database**
3. Find the **Connection Pooling** section
4. Copy the **Session** mode connection string
5. The format will be: `postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`

### Connection String Format

```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

Where:
- `PROJECT_REF`: Your Supabase project reference ID
- `PASSWORD`: Your database password
- `REGION`: Your project's AWS region (e.g., us-east-1, eu-west-1)

## Code Changes

### Dependencies

**Added:**
```txt
asyncpg==0.29.0  # PostgreSQL async driver
```

**Kept (optional):**
```txt
supabase==2.3.0  # Still available for auth/storage operations if needed
```

### Database Client

The `DatabaseClient` class now:
- Uses `asyncpg.Pool` for connection pooling
- Provides async context managers for connections
- Executes raw SQL queries instead of using Supabase client methods

### Repository Layer

Session repository methods now use:
- Raw SQL queries with parameterized statements
- Proper handling of PostgreSQL-specific types (JSONB)
- Direct connection pool access

## Migration Steps

1. **Update Dependencies**
   ```bash
   pip install asyncpg==0.29.0
   ```

2. **Get Session Pooler Connection String**
   - Follow the steps above to get your connection string from Supabase dashboard

3. **Update Environment Variables**
   ```env
   # Replace these old variables
   # SUPABASE_URL=https://your-project.supabase.co
   # SUPABASE_KEY=your-supabase-anon-key
   
   # With this new variable
   SUPABASE_POOLER_CONNECTION_STRING=postgresql://postgres.your-project:password@aws-0-region.pooler.supabase.com:6543/postgres
   ```

4. **Test the Connection**
   ```bash
   # Start the application
   uvicorn app.main:app --reload
   
   # Test health endpoint
   curl http://localhost:8000/api/v1/health
   ```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify the connection string format
   - Ensure your IP is allowlisted in Supabase (or use 0.0.0.0/0 for development)
   - Check that Session Pooler is enabled in your Supabase project

2. **Authentication Failed**
   - Verify your database password is correct
   - Ensure you're using the correct project reference ID

3. **SSL/TLS Issues**
   - Session pooler connections use SSL by default
   - If you encounter SSL issues, you can add `?sslmode=require` to the connection string

4. **Connection Pool Exhaustion**
   - Monitor connection pool usage in logs
   - Adjust pool size settings if needed (currently set to max 10 connections)

### Verification Steps

1. **Check Database Connection**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Test Session Operations**
   ```bash
   # Test session retrieval (replace 123 with actual session ID)
   curl -X POST http://localhost:8000/api/v1/similarity/123 \
     -H "Content-Type: application/json" \
     -d '{"reference_text": "test reference text"}'
   ```

3. **Monitor Logs**
   - Check application logs for connection pool messages
   - Look for successful "Database connection pool created" messages

## Performance Considerations

### Connection Pool Settings

Current settings (in `database.py`):
```python
pool = await asyncpg.create_pool(
    dsn=settings.supabase_pooler_connection_string,
    min_size=1,      # Minimum connections
    max_size=10,     # Maximum connections
    command_timeout=60,
    server_settings={'jit': 'off'}
)
```

### Tuning Recommendations

- **Development**: min_size=1, max_size=5
- **Production**: min_size=5, max_size=20 (adjust based on load)
- **High Load**: Consider increasing max_size and monitoring connection usage

## Rollback Plan

If you need to rollback to the standard Supabase client:

1. Revert environment variables to use `SUPABASE_URL` and `SUPABASE_KEY`
2. Restore the original `database.py` and `session_repository.py` files
3. Remove `asyncpg` dependency if not needed elsewhere

## Support

For issues related to:
- **Session Pooler Setup**: Check Supabase documentation
- **Connection Issues**: Verify network access and credentials
- **Performance**: Monitor connection pool metrics and adjust settings
- **Application Errors**: Check application logs for detailed error messages