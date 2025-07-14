from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from config.settings import settings
from config.logging_config import setup_logging, get_logger
from api.routes.upload import router as upload_router
from api.routes.download import router as download_router
from api.middleware.error_handler import error_handler_middleware
from api.middleware.logging_middleware import logging_middleware
from services.storage_service import StorageService

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
    lifespan=lifespan
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
app.middleware("http")(error_handler_middleware)
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(upload_router)
app.include_router(download_router)

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
                "version": settings.API_VERSION
            }
        else:
            return {
                "status": "initializing",
                "services": {},
                "version": settings.API_VERSION
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
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    ) 