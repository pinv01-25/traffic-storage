import json
import requests
from typing import Dict, Any
from config.settings import settings
from config.logging_config import get_logger
from utils.exceptions import IPFSError

logger = get_logger(__name__)

class IPFSService:
    """Service for interacting with IPFS via Pinata."""
    
    def __init__(self):
        self.api_url = settings.IPFS_API_URL
        self.timeout = settings.IPFS_TIMEOUT
        self.pinata_jwt = settings.PINATA_JWT
        self.pinata_url = settings.PINATA_URL
    
    def upload_json(self, data: Dict[str, Any]) -> str:
        """
        Upload JSON data to IPFS via Pinata.
        
        Args:
            data: JSON data to upload
            
        Returns:
            CID (Content Identifier) of the uploaded data
            
        Raises:
            IPFSError: If upload fails
        """
        try:
            logger.info(f"Starting upload to Pinata API: {self.api_url}")
            logger.debug(f"Uploading JSON data to Pinata: {len(json.dumps(data))} bytes")
            
            if not self.pinata_jwt:
                raise IPFSError("PINATA_JWT not configured")
            
            # Prepare headers for Pinata API
            headers = {
                'Authorization': f'Bearer {self.pinata_jwt}',
                'Content-Type': 'application/json'
            }
            
            # Prepare payload for Pinata
            payload = {
                'pinataMetadata': {
                    'name': 'traffic-data.json',
                    'keyvalues': {
                        'type': 'traffic-data',
                        'timestamp': str(data.get('timestamp', ''))
                    }
                },
                'pinataContent': data
            }
            
            logger.debug(f"Making POST request to: {self.api_url}/pinning/pinJSONToIPFS")
            
            # Upload to Pinata
            response = requests.post(
                f"{self.api_url}/pinning/pinJSONToIPFS",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            cid = result['IpfsHash']
            
            logger.info(f"Successfully uploaded data to Pinata with CID: {cid}")
            return cid
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Pinata upload request failed: {str(e)}")
            raise IPFSError(f"Failed to upload to Pinata: {str(e)}")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Pinata response parsing failed: {str(e)}")
            raise IPFSError(f"Failed to parse Pinata response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during Pinata upload: {str(e)}")
            raise IPFSError(f"Unexpected error during Pinata upload: {str(e)}")
    
    def download_json(self, cid: str) -> Dict[str, Any]:
        """
        Download JSON data from IPFS via Pinata gateway.
        
        Args:
            cid: Content Identifier of the data to download
            
        Returns:
            Downloaded JSON data
            
        Raises:
            IPFSError: If download fails
        """
        try:
            # Use Pinata gateway if available, otherwise fallback to public gateway
            gateway_url = self.pinata_url or "https://gateway.pinata.cloud"
            
            logger.info(f"Starting download from gateway: {gateway_url}")
            logger.debug(f"Downloading JSON data from Pinata gateway with CID: {cid}")
            
            # Use a shorter timeout for downloads to fail fast
            download_timeout = min(10, self.timeout)  # Max 10 seconds for downloads
            
            # Download from IPFS via gateway
            download_url = f"{gateway_url}/ipfs/{cid}"
            logger.debug(f"Making GET request to: {download_url}")
            
            response = requests.get(
                download_url,
                timeout=download_timeout
            )
            response.raise_for_status()
            
            # Parse JSON data
            data = response.json()
            
            logger.info(f"Successfully downloaded data from Pinata gateway with CID: {cid}")
            return data
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Pinata gateway download timeout for CID {cid}: {str(e)}")
            raise IPFSError(f"Download timeout from Pinata gateway: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Pinata gateway download request failed for CID {cid}: {str(e)}")
            raise IPFSError(f"Failed to download from Pinata gateway: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Pinata gateway response JSON parsing failed for CID {cid}: {str(e)}")
            raise IPFSError(f"Failed to parse downloaded JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during Pinata gateway download for CID {cid}: {str(e)}")
            raise IPFSError(f"Unexpected error during Pinata gateway download: {str(e)}")
    
    def check_connectivity(self) -> bool:
        """
        Check Pinata connectivity.
        
        Returns:
            True if Pinata is accessible
        """
        try:
            if not self.pinata_jwt:
                logger.warning("PINATA_JWT not configured")
                return False
                
            headers = {
                'Authorization': f'Bearer {self.pinata_jwt}'
            }
            
            logger.debug(f"Checking Pinata connectivity to: {self.api_url}/data/testAuthentication")
            
            response = requests.get(
                f"{self.api_url}/data/testAuthentication",
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            logger.debug("Pinata connectivity check successful")
            return True
        except Exception as e:
            logger.warning(f"Pinata connectivity check failed: {str(e)}")
            return False 