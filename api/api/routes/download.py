from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from models.schemas import DownloadRequest
from services.storage_service import StorageService
from config.logging_config import get_logger, log_success, log_error
from utils.exceptions import DownloadError

logger = get_logger(__name__, service_name="traffic_storage")
router = APIRouter(prefix="/download", tags=["download"])

# Initialize storage service
storage_service = StorageService()

@router.post("/")
async def download_metadata(body: DownloadRequest) -> Dict[str, Any]:
    """
    Download data from IPFS based on traffic_light_id, timestamp, and type.
    Expects Unix timestamps (int).
    Returns data in the format it was stored (unified 2.0 format for sensor data).
    """
    try:
        logger.info(f"Download request received for {body.type} data, traffic_light_id: {body.traffic_light_id}")
        
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