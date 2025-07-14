from pydantic import BaseModel, Field, validator
from typing import List, Literal
from models.enums import DataVersion, DataTypeString

class DataBatch(BaseModel):
    """Schema for data (1-10 sensors)."""
    version: str = DataVersion.V2_0
    type: Literal[DataTypeString.DATA]
    timestamp: int
    traffic_light_id: str
    sensors: List[dict] = Field(..., min_items=1, max_items=10)

    @validator('sensors')
    def validate_sensors_reference_id(cls, v, values):
        """Validate that the reference traffic_light_id is present in sensors."""
        if 'traffic_light_id' in values:
            reference_id = values['traffic_light_id']
            sensor_ids = [sensor.get('traffic_light_id') for sensor in v]
            if reference_id not in sensor_ids:
                raise ValueError(f'traffic_light_id {reference_id} must be present in sensors list')
        return v

class OptimizationBatch(BaseModel):
    """Schema for optimization (1-10 optimizations)."""
    version: str = DataVersion.V2_0
    type: Literal[DataTypeString.OPTIMIZATION]
    timestamp: int
    traffic_light_id: str
    optimizations: List[dict] = Field(..., min_items=1, max_items=10)

    @validator('optimizations')
    def validate_optimizations_reference_id(cls, v, values):
        """Validate that the reference traffic_light_id is present in optimizations."""
        if 'traffic_light_id' in values:
            reference_id = values['traffic_light_id']
            optimization_ids = [opt.get('traffic_light_id') for opt in v]
            if reference_id not in optimization_ids:
                raise ValueError(f'traffic_light_id {reference_id} must be present in optimizations list')
        return v

class DownloadRequest(BaseModel):
    """Schema for download requests."""
    traffic_light_id: str
    timestamp: int
    type: Literal[DataTypeString.DATA, DataTypeString.OPTIMIZATION]

# Union type for upload models - unified approach for both single and batch
UploadModel = DataBatch | OptimizationBatch 