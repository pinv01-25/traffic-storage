import os
import requests

PINATA_JWT = os.getenv("PINATA_JWT")
PINATA_URL = os.getenv("PINATA_URL")

if not PINATA_JWT:
    raise RuntimeError("Missing PINATA_JWT in environment")
if not PINATA_URL:
    raise RuntimeError("Missing PINATA_URL in environment")

def upload_json_to_ipfs(data: dict) -> str:
    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type": "application/json"
    }
    payload = {
        "pinataContent": data,
        "pinataMetadata": { "name": "metadata.json" }
    }

    response = requests.post(
        "https://api.pinata.cloud/pinning/pinJSONToIPFS",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()["IpfsHash"]

def download_json_from_ipfs(cid: str) -> dict:
    response = requests.get(f"{PINATA_URL}/ipfs/{cid}")
    response.raise_for_status()
    return response.json()
