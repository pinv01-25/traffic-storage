import time
from fastapi import Request
from config.logging_config import get_logger, log_request

logger = get_logger(__name__, service_name="traffic_storage")

async def logging_middleware(request: Request, call_next):
    """
    Middleware for logging request and response information.
    """
    start_time = time.time()
    
    # Log request
    log_request(logger, request.method, str(request.url))
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response with status and duration
    log_request(logger, request.method, str(request.url), response.status_code, process_time)
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response 