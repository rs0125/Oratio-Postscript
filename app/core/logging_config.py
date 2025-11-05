"""
Structured logging configuration for the Speech Similarity API.

This module provides comprehensive logging setup with:
- Structured JSON logging
- Correlation ID support
- Performance metrics
- Log level configuration
- Request/response logging
"""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import json
import uuid
from contextvars import ContextVar

from app.core.config import settings

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter to add correlation ID to log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = correlation_id.get() or "unknown"
        return True


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', 'unknown'),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'processing_time'):
            log_data['processing_time'] = record.processing_time
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        if hasattr(record, 'user_agent'):
            log_data['user_agent'] = record.user_agent
        if hasattr(record, 'query_params'):
            log_data['query_params'] = record.query_params
        if hasattr(record, 'exception_type'):
            log_data['exception_type'] = record.exception_type
        if hasattr(record, 'exception_message'):
            log_data['exception_message'] = record.exception_message
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add any additional custom fields
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_') and key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    """
    # Import settings here to avoid circular imports
    from app.core.config import settings
    
    # Determine log level
    log_level = settings.log_level if hasattr(settings, 'log_level') else ("DEBUG" if settings.debug else "INFO")
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "structured" if (hasattr(settings, 'structured_logging') and settings.structured_logging) else "simple",
                "filters": ["correlation_id"],
                "level": log_level,
            }
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)


def get_correlation_id() -> str:
    """
    Get the current correlation ID or generate a new one.
    
    Returns:
        Current correlation ID or a new UUID if none exists
    """
    current_id = correlation_id.get()
    if current_id is None:
        current_id = str(uuid.uuid4())
        correlation_id.set(current_id)
    return current_id


def set_correlation_id(new_id: str) -> None:
    """
    Set the correlation ID for the current context.
    
    Args:
        new_id: The correlation ID to set
    """
    correlation_id.set(new_id)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Performance metrics tracking
class PerformanceMetrics:
    """
    Simple in-memory performance metrics tracking.
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests": {
                "total": 0,
                "by_method": {},
                "by_status": {},
                "by_endpoint": {},
            },
            "response_times": {
                "total_time": 0.0,
                "count": 0,
                "average": 0.0,
                "min": float('inf'),
                "max": 0.0,
            },
            "errors": {
                "total": 0,
                "by_type": {},
            }
        }
    
    def record_request(self, method: str, endpoint: str, status_code: int, processing_time: float) -> None:
        """Record request metrics."""
        # Update request counts
        self.metrics["requests"]["total"] += 1
        self.metrics["requests"]["by_method"][method] = self.metrics["requests"]["by_method"].get(method, 0) + 1
        self.metrics["requests"]["by_status"][str(status_code)] = self.metrics["requests"]["by_status"].get(str(status_code), 0) + 1
        self.metrics["requests"]["by_endpoint"][endpoint] = self.metrics["requests"]["by_endpoint"].get(endpoint, 0) + 1
        
        # Update response time metrics
        self.metrics["response_times"]["total_time"] += processing_time
        self.metrics["response_times"]["count"] += 1
        self.metrics["response_times"]["average"] = self.metrics["response_times"]["total_time"] / self.metrics["response_times"]["count"]
        self.metrics["response_times"]["min"] = min(self.metrics["response_times"]["min"], processing_time)
        self.metrics["response_times"]["max"] = max(self.metrics["response_times"]["max"], processing_time)
        
        # Record errors
        if status_code >= 400:
            self.metrics["errors"]["total"] += 1
    
    def record_error(self, error_type: str) -> None:
        """Record error metrics."""
        self.metrics["errors"]["by_type"][error_type] = self.metrics["errors"]["by_type"].get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        # Fix infinite min value if no requests recorded
        if self.metrics["response_times"]["min"] == float('inf'):
            self.metrics["response_times"]["min"] = 0.0
        
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.__init__()


# Global metrics instance
performance_metrics = PerformanceMetrics()