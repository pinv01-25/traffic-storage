from typing import List, Literal

from api.models.enums import DataTypeString, DataVersion
from pydantic import BaseModel, Field, model_validator


class DataBatch(BaseModel):
    """Schema for data (1-10 sensors)."""

    version: str = DataVersion.V2_0
    type: Literal[DataTypeString.DATA]
    timestamp: int
    traffic_light_id: str
    sensors: List[dict] = Field(..., min_items=1, max_items=10)

    @model_validator(mode="after")
    def validate_sensors_reference_id(self):
        """Validate that the reference traffic_light_id is present in sensors."""
        reference_id = self.traffic_light_id
        sensor_ids = [sensor.get("traffic_light_id") for sensor in self.sensors]
        if reference_id not in sensor_ids:
            raise ValueError(
                f"traffic_light_id {reference_id} must be present in sensors list"
            )
        return self


class OptimizationBatch(BaseModel):
    """Schema for optimization (1-10 optimizations)."""

    version: str = DataVersion.V2_0
    type: Literal[DataTypeString.OPTIMIZATION]
    timestamp: int
    traffic_light_id: str
    optimizations: List[dict] = Field(..., min_items=1, max_items=10)

    @model_validator(mode="after")
    def validate_optimizations_reference_id(self):
        """Validate that the reference traffic_light_id is present in optimizations."""
        reference_id = self.traffic_light_id
        optimization_ids = [opt.get("traffic_light_id") for opt in self.optimizations]
        if reference_id not in optimization_ids:
            raise ValueError(
                f"traffic_light_id {reference_id} must be present in optimizations list"
            )
        return self


class DownloadRequest(BaseModel):
    """Schema for download requests."""

    traffic_light_id: str
    timestamp: int
    type: Literal[DataTypeString.DATA, DataTypeString.OPTIMIZATION]


# Union type for upload models - unified approach for both single and batch
UploadModel = DataBatch | OptimizationBatch  # noqa: E501
