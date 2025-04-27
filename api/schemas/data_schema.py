from pydantic import BaseModel
from typing import List

class TrafficMetrics(BaseModel):
    vehicles_per_minute: int
    avg_speed_kmh: float
    avg_circulation_time_sec: float
    density: float

class VehicleStats(BaseModel):
    motorcycle: int
    car: int
    bus: int
    truck: int

class TrafficData(BaseModel):
    version: str
    type: str = "data"
    timestamp: str
    traffic_light_id: str
    controlled_edges: List[str]
    metrics: TrafficMetrics
    vehicle_stats: VehicleStats
