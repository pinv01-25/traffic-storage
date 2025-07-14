from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from models.schemas import UploadModel
from services.storage_service import StorageService
from config.logging_config import get_logger, log_success, log_error
from utils.exceptions import UploadError, ValidationError

logger = get_logger(__name__, service_name="traffic_storage")
router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize storage service
storage_service = StorageService()

@router.post("/")
async def upload_metadata(metadata: UploadModel = Body(...)) -> Dict[str, Any]:
    """
    Upload metadata to IPFS and store reference in BlockDAG.
    Supports both optimization data and sensor data (single or batch).
    Expects Unix timestamps (int).
    """
    try:
        logger.info(f"Upload request received for {metadata.type} data, traffic_light_id: {metadata.traffic_light_id}")
        
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