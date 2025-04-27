from api.schemas.data_schema import TrafficData
from api.schemas.optimization_schema import OptimizationData

def validate_payload(payload: dict) -> None:
    """
    Valida el payload usando el modelo correcto de Pydantic
    según su campo "type".
    """
    if "type" not in payload:
        raise ValueError("Missing 'type' field in payload")

    payload_type = payload["type"].lower()

    if payload_type == "data":
        TrafficData(**payload)  # Esto lanza un error si no cumple el schema
    elif payload_type == "optimization":
        OptimizationData(**payload)
    else:
        raise ValueError(f"Unknown payload type: {payload_type}")
