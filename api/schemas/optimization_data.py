from pydantic import BaseModel

class OptimizationDetails(BaseModel):
    green_time_sec: int
    red_time_sec: int

class ImpactDetails(BaseModel):
    original_congestion: int
    optimized_congestion: int
    original_category: str
    optimized_category: str

class OptimizationData(BaseModel):
    version: str
    type: str = "optimization"
    timestamp: str
    traffic_light_id: str
    optimization: OptimizationDetails
    impact: ImpactDetails
