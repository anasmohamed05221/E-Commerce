"""
Logging utility functions and helpers.
"""

import logging
from typing import Any, Dict, Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger
        
    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from log data.
    
    Args:
        data: Dictionary that may contain sensitive fields
        
    Returns:
        Sanitized dictionary safe for logging
        
    Why?
    - Prevent passwords, tokens, credit cards from appearing in logs
    - GDPR compliance
    - Security best practice
    """
    sensitive_fields = {
        'password', 'token', 'secret', 'api_key', 'access_token', 
        'refresh_token', 'credit_card', 'cvv', 'ssn'
    }
    
    sanitized = data.copy()
    
    for key, value in sanitized.items():
        # Check if key contains sensitive field name (case-insensitive)
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            if isinstance(value, str):
                # For tokens, show first 8 chars for debugging
                if 'token' in key.lower() and len(value) > 8:
                    sanitized[key] = f"{value[:8]}..."
                else:
                    # For passwords, completely redact
                    sanitized[key] = "***REDACTED***"
        
        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
    
    return sanitized


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """
    Log HTTP request in a structured format.
    
    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: Authenticated user ID (if any)
        extra: Additional context to log
        
    Usage:
        log_request(logger, "POST", "/api/auth/login", 200, 45.2, user_id=123)
    """
    log_data = {
        "http_method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if extra:
        # Sanitize extra data before logging
        log_data.update(sanitize_log_data(extra))
    
    # Choose log level based on status code
    if status_code >= 500:
        logger.error(f"{method} {path} - {status_code}", extra=log_data)
    elif status_code >= 400:
        logger.warning(f"{method} {path} - {status_code}", extra=log_data)
    else:
        logger.info(f"{method} {path} - {status_code}", extra=log_data)


def log_database_query(
    logger: logging.Logger,
    query_type: str,
    table: str,
    duration_ms: float,
    rows_affected: Optional[int] = None
):
    """
    Log database operations in a structured format.
    
    Args:
        logger: Logger instance
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Query duration in milliseconds
        rows_affected: Number of rows affected (for INSERT/UPDATE/DELETE)
        
    Note: Only use in development (DEBUG level)
    
    Usage:
        log_database_query(logger, "SELECT", "users", 12.5)
    """
    log_data = {
        "query_type": query_type,
        "table": table,
        "duration_ms": round(duration_ms, 2)
    }
    
    if rows_affected is not None:
        log_data["rows_affected"] = rows_affected
    
    # Warn on slow queries (> 1 second)
    if duration_ms > 1000:
        logger.warning(
            f"Slow {query_type} query on {table}",
            extra=log_data
        )
    else:
        logger.debug(
            f"{query_type} query on {table}",
            extra=log_data
        )