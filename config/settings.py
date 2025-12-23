from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Support both old format (RPC_URL, PRIVATE_KEY, CHAIN_ID) and new format
    BLOCKDAG_RPC_URL: str = Field(
        default="https://rpc.primordial.bdagscan.com",
        alias="RPC_URL",
        validation_alias="RPC_URL",
    )
    BLOCKDAG_CHAIN_ID: int = Field(default=1043, alias="CHAIN_ID", validation_alias="CHAIN_ID")
    BLOCKDAG_PRIVATE_KEY: Optional[str] = Field(
        default=None, alias="PRIVATE_KEY", validation_alias="PRIVATE_KEY"
    )
    BLOCKDAG_CONTRACT_ADDRESS: str = "0xC3d520EBE9A9F52FC5E1519f17F5a9A01d8ac68f"

    # Data Validation
    MAX_SENSORS_PER_BATCH: int = 10
    MIN_SENSORS_PER_BATCH: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    # Data Types Mapping
    DATA_TYPE_MAP: dict = {"data": 0, "optimization": 1}

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields from .env
        populate_by_name=True,  # Allow both field name and alias
    )

    @field_validator("BLOCKDAG_RPC_URL", mode="before")
    @classmethod
    def validate_rpc_url(cls, v):
        """Convert empty strings to None to use default value."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("BLOCKDAG_PRIVATE_KEY", mode="before")
    @classmethod
    def validate_private_key(cls, v):
        """Convert empty strings to None."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


# Global settings instance
settings = Settings()
