from services.ipfs_service import IPFSService
from services.blockdag_service import BlockDAGService
from datetime import datetime

TYPE_TO_ENUM = {
    "data": 0,
    "optimization": 1,
}

# Initialize services
ipfs_service = IPFSService()
blockdag_service = BlockDAGService()

async def upload_and_register(payload: dict):
    payload_type = payload["type"].lower()
    if payload_type not in TYPE_TO_ENUM:
        raise ValueError(f"Unknown type {payload_type}")

    # Subir a IPFS
    cid = ipfs_service.upload_json(payload)

    # Convert timestamp to Unix timestamp
    unix_timestamp = convert_to_unix_timestamp(payload["timestamp"])

    # Registrar en BlockDAG
    await blockdag_service.store_metadata(
        traffic_light_id=payload["traffic_light_id"],
        timestamp=unix_timestamp,
        data_type=TYPE_TO_ENUM[payload_type],
        cid=cid
    )

    print(f"Uploaded and registered payload → CID: {cid}")

async def download_and_verify(traffic_light_id: str, timestamp: int, data_type_enum: int):
    cid = await blockdag_service.fetch_metadata(traffic_light_id, timestamp, data_type_enum)
    payload = ipfs_service.download_json(cid)
    return payload

def convert_to_unix_timestamp(timestamp_str: str) -> int:
    """Convert ISO timestamp string to Unix timestamp."""
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    return int(dt.timestamp())