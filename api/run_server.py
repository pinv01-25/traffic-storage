#!/usr/bin/env python3
"""
Server runner for the modular traffic-storage API
"""

import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Main function to run the server."""
    logger.info("Starting Traffic Storage API server...")
    logger.info(f"Host: {settings.API_HOST}")
    logger.info(f"Port: {settings.API_PORT}")
    logger.info(f"Debug: {settings.DEBUG}")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main() 