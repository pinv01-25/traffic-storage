import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Centralized configuration settings for the traffic-storage service."""
    
    # API Configuration
    API_TITLE: str = "Traffic Storage API"
    API_VERSION: str = "2.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # IPFS Configuration (Pinata)
    IPFS_API_URL: str = "https://api.pinata.cloud"
    IPFS_TIMEOUT: int = 30
    PINATA_JWT: Optional[str] = None
    PINATA_URL: Optional[str] = None
    
    # BlockDAG Configuration
    BLOCKDAG_RPC_URL: str = "https://rpc.primordial.bdagscan.com"
    BLOCKDAG_CHAIN_ID: int = 1043
    BLOCKDAG_PRIVATE_KEY: Optional[str] = None
    BLOCKDAG_CONTRACT_ADDRESS: str = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f"
    
    # Data Validation
    MAX_SENSORS_PER_BATCH: int = 10
    MIN_SENSORS_PER_BATCH: int = 1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # Data Types Mapping
    DATA_TYPE_MAP: dict = {
        "data": 0,
        "optimization": 1
    }
    
    class Config:
        env_file = "../.env"
        case_sensitive = True

# Global settings instance
settings = Settings() 