from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from config.logging_config import get_logger, log_error

logger = get_logger(__name__, service_name="traffic_storage")

async def error_handler_middleware(request: Request, call_next):
    """
    Middleware for handling errors and providing consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log unexpected errors
        log_error(logger, e, f"{request.method} {request.url}")
        
        # Return consistent error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "path": str(request.url)
            }
        ) 