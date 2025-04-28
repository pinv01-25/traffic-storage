from api.scripts.validator import validate_payload
from api.modules.ipfs.ipfs_manager import upload_json_to_ipfs, download_json_from_ipfs
from api.modules.blockdag.blockdag_client import store_metadata_in_blockdag, fetch_metadata_from_blockdag
from datetime import datetime

TYPE_TO_ENUM = {
    "data": 0,
    "optimization": 1,
}

def convert_to_unix_timestamp(timestamp_str: str) -> int:
    # Si tus timestamps tienen el timezone como "-03" debes manejarlo.
    # Aquí simplificamos ignorando el timezone.
    ts = datetime.fromisoformat(timestamp_str.replace("-03", ""))
    return int(ts.timestamp())

async def upload_and_register(payload: dict):
    # Validar con Pydantic
    validate_payload(payload)

    payload_type = payload["type"].lower()
    if payload_type not in TYPE_TO_ENUM:
        raise ValueError(f"Unknown type {payload_type}")

    # Subir a IPFS
    cid = await upload_json_to_ipfs(payload)

    # Convertir timestamp a Unix
    converted_timestamp = convert_to_unix_timestamp(payload["timestamp"])

    # Registrar en BlockDAG
    await store_metadata_in_blockdag(
        traffic_light_id=payload["traffic_light_id"],
        timestamp=converted_timestamp,
        data_type=TYPE_TO_ENUM[payload_type],
        cid=cid
    )

    print(f"Uploaded and registered payload → CID: {cid}")

async def download_and_verify(traffic_light_id: str, timestamp: int, data_type_enum: int):
    cid = await fetch_metadata_from_blockdag(traffic_light_id, timestamp, data_type_enum)
    payload = await download_json_from_ipfs(cid)
    return payload