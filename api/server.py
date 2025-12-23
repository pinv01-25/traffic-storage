"""
Traffic Storage API Server

Main FastAPI application for traffic data storage service.
Consolidates server setup and routes following SOLID, KISS, and DRY principles.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from config.logging_config import log_error, log_success, setup_logging
from config.settings import settings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from modules.services.storage import StorageService
from modules.utils import DownloadError, UploadError, ValidationError

from api.models.schemas import DownloadRequest, UploadModel

# Setup unified logging
logger = setup_logging("traffic_storage", level=settings.LOG_LEVEL)

# Global storage service instance
storage_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global storage_service

    # Startup
    logger.info("Starting Traffic Storage API...")
    storage_service = StorageService()

    # Check services health
    health_status = storage_service.check_services_health()
    logger.info(f"Services health check: {health_status}")

    yield

    # Shutdown
    logger.info("Shutting down Traffic Storage API...")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add custom middleware
@app.middleware("http")
async def error_handler_middleware(request, call_next):
    """Middleware for handling errors and providing consistent error responses."""
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
                "path": str(request.url),
            },
        )


@app.middleware("http")
async def logging_middleware(request, call_next):
    """Middleware for logging request and response information."""
    import time

    from config.logging_config import log_request

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


# Routes
@app.post("/upload")
async def upload_metadata(metadata: UploadModel) -> Dict[str, Any]:
    """
    Upload metadata to IPFS and store reference in BlockDAG.
    Supports both optimization data and sensor data (single or batch).
    Expects Unix timestamps (int).
    """
    try:
        logger.info(
            f"Upload request received for {metadata.type} data, traffic_light_id: {metadata.traffic_light_id}"
        )

        # Upload metadata using storage service
        result = await storage_service.upload_metadata(metadata)

        log_success(logger, f"Upload completed for traffic_light_id: {metadata.traffic_light_id}")
        return result

    except ValidationError as e:
        log_error(logger, e, "upload validation")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except UploadError as e:
        log_error(logger, e, "upload operation")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    except Exception as e:
        log_error(logger, e, "upload operation")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/download")
async def download_metadata(body: DownloadRequest) -> Dict[str, Any]:
    """
    Download data from IPFS based on traffic_light_id, timestamp, and type.
    Expects Unix timestamps (int).
    Returns data in the format it was stored (unified 2.0 format for sensor data).
    """
    try:
        logger.info(
            f"Download request received for {body.type} data, traffic_light_id: {body.traffic_light_id}"
        )

        # Download metadata using storage service
        result = await storage_service.download_metadata(body)

        log_success(logger, f"Download completed for traffic_light_id: {body.traffic_light_id}")
        return result

    except DownloadError as e:
        log_error(logger, e, "download operation")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    except Exception as e:
        log_error(logger, e, "download operation")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/healthcheck")
async def healthcheck() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns the status of all services.
    """
    try:
        if storage_service:
            health_status = storage_service.check_services_health()
            return {
                "status": "ok",
                "services": health_status,
                "version": settings.API_VERSION,
            }
        else:
            return {
                "status": "initializing",
                "services": {},
                "version": settings.API_VERSION,
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "message": "Traffic Storage API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }


def main():
    """Main function to run the server."""
    logger.info("Starting Traffic Storage API server...")
    logger.info(f"Host: {settings.API_HOST}")
    logger.info(f"Port: {settings.API_PORT}")
    logger.info(f"Debug: {settings.DEBUG}")

    uvicorn.run(
        "api.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
