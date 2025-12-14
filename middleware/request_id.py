"""
Request ID middleware for tracking requests across the application.

Why?
- Trace a single user's request through multiple services/functions
- Correlate all logs related to one request
- Essential for debugging complex issues
"""

import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.
    
    How it works:
    1. Request comes in
    2. Generate UUID (or use client-provided X-Request-ID header)
    3. Store in request.state for access in route handlers
    4. Add to response headers so client can reference it
    5. Include in all logs via logging filter
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request and add request ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler in chain
            
        Returns:
            Response with X-Request-ID header
        """
        # Check if client provided a request ID (useful for distributed tracing)
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            # Generate new UUID if not provided
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in route handlers
        request.state.request_id = request_id
        
        # Add to logging context using a filter
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            # Process the request
            response: Response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)



def get_request_id(request: Request) -> str:
    """
    Helper function to get request ID from request state.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Request ID string, or "no-request-id" if not found
        
    Usage in route handlers:
        from middleware.request_id import get_request_id
        
        @router.get("/users")
        async def get_users(request: Request):
            req_id = get_request_id(request)
            logger.info("Fetching users", extra={"request_id": req_id})
    """
    return getattr(request.state, "request_id", "no-request-id")