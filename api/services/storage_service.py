from typing import Dict, Any, Union
from config.settings import settings
from config.logging_config import get_logger
from models.schemas import UploadModel, DownloadRequest
from utils.exceptions import StorageError, ValidationError, UploadError, DownloadError
from utils.validators import validate_data_payload
from services.ipfs_service import IPFSService
from services.blockdag_service import BlockDAGService

logger = get_logger(__name__, service_name="traffic_storage")

class StorageService:
    """Main storage service that orchestrates IPFS and BlockDAG operations."""
    
    def __init__(self):
        self.ipfs_service = IPFSService()
        self.blockdag_service = BlockDAGService()
    
    async def upload_metadata(self, metadata: UploadModel) -> Dict[str, Any]:
        """
        Upload metadata to IPFS and store reference in BlockDAG.
        
        Args:
            metadata: Data to upload (optimization or sensor data)
            
        Returns:
            Upload response with CID and metadata
            
        Raises:
            UploadError: If upload fails
        """
        try:
            logger.info(f"Starting upload for {metadata.type} data, traffic_light_id: {metadata.traffic_light_id}")
            
            # Validate data payload
            validate_data_payload(metadata.dict())
            logger.debug("Data validation passed")
            
            # Upload to IPFS
            cid = self.ipfs_service.upload_json(metadata.dict())
            logger.debug(f"Data uploaded to IPFS with CID: {cid}")
            
            # Get data type for BlockDAG
            data_type = settings.DATA_TYPE_MAP[metadata.type]
            
            # Store reference in BlockDAG
            await self.blockdag_service.store_metadata(
                traffic_light_id=metadata.traffic_light_id,
                timestamp=metadata.timestamp,
                data_type=data_type,
                cid=cid
            )
            logger.debug(f"Metadata stored in BlockDAG for traffic_light_id: {metadata.traffic_light_id}")
            
            # Prepare response
            response = self._prepare_upload_response(metadata, cid)
            
            logger.info(f"Upload completed successfully for {metadata.type} data, CID: {cid}")
            return response
            
        except ValidationError as e:
            logger.error(f"Data validation failed: {str(e)}")
            raise UploadError(f"Data validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise UploadError(f"Upload failed: {str(e)}")
    
    async def download_metadata(self, request: DownloadRequest) -> Dict[str, Any]:
        """
        Download metadata from IPFS based on BlockDAG reference.
        
        Args:
            request: Download request with traffic_light_id, timestamp, and type
            
        Returns:
            Downloaded data
            
        Raises:
            DownloadError: If download fails
        """
        try:
            logger.info(f"Starting download for {request.type} data, traffic_light_id: {request.traffic_light_id}")
            
            # Get data type for BlockDAG
            data_type = settings.DATA_TYPE_MAP[request.type]
            
            # Fetch CID from BlockDAG
            cid = await self.blockdag_service.fetch_metadata(
                traffic_light_id=request.traffic_light_id,
                timestamp=request.timestamp,
                data_type=data_type
            )
            logger.debug(f"Retrieved CID from BlockDAG: {cid}")
            
            # Download from IPFS
            data = self.ipfs_service.download_json(cid)
            logger.debug(f"Data downloaded from IPFS with CID: {cid}")
            
            logger.info(f"Download completed successfully for {request.type} data, CID: {cid}")
            return data
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise DownloadError(f"Download failed: {str(e)}")
    
    def _prepare_upload_response(self, metadata: UploadModel, cid: str) -> Dict[str, Any]:
        """
        Prepare upload response based on data type.
        
        Args:
            metadata: Uploaded metadata
            cid: Content Identifier from IPFS
            
        Returns:
            Formatted response
        """
        base_response = {
            "cid": cid,
            "type": metadata.type,
            "timestamp": metadata.timestamp,
            "traffic_light_id": metadata.traffic_light_id
        }
        
        if metadata.type == "data":
            response = {
                "message": "Data uploaded successfully",
                **base_response
            }
            
            # Add sensors count for batch data
            if hasattr(metadata, 'sensors'):
                response["sensors_count"] = len(metadata.sensors)
                
        else:  # optimization
            response = {
                "message": "Optimization metadata uploaded successfully",
                **base_response
            }
        
        return response
    
    def check_services_health(self) -> Dict[str, bool]:
        """
        Check health of all storage services.
        
        Returns:
            Dictionary with health status of each service
        """
        health_status = {
            "ipfs": self.ipfs_service.check_connectivity(),
            "blockdag": self.blockdag_service.check_connectivity()
        }
        
        logger.info(f"Health check results: {health_status}")
        return health_status 