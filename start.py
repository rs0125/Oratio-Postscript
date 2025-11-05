#!/usr/bin/env python3
"""
Production startup script for Render deployment.
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )