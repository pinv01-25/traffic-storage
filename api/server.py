from datetime import datetime
from fastapi import FastAPI, HTTPException, Body, Query
from pydantic import BaseModel
from typing import  Literal
import os
import glob
import json
from api.database import database
from api.models.metadata_index import metadata_index
from sqlalchemy import insert, select
from fastapi import Request
from api.modules.ipfs.ipfs_manager import upload_json_to_ipfs, download_json_from_ipfs
from api.modules.blockdag.blockdag_client import store_metadata_in_blockdag, fetch_metadata_from_blockdag
from api.storage_manager import convert_to_unix_timestamp
from api.scripts.generate_jsons import generate_jsons
from api.scripts.validator import validate_payload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(BASE_DIR, "input")

DATA_TYPE_MAP = {
    "data": 0,
    "optimization": 1
}

# --- FastAPI instance ---
app = FastAPI(title="Traffic Storage API", version="2.0")

# --- Pydantic models ---

class TrafficDataMetadata(BaseModel):
    version: str = "1.0"
    type: Literal["data"]
    timestamp: str
    traffic_light_id: str
    controlled_edges: list[str]
    metrics: dict
    vehicle_stats: dict

class OptimizationMetadata(BaseModel):
    version: str = "1.0"
    type: Literal["optimization"]
    timestamp: str
    traffic_light_id: str
    optimization: dict
    impact: dict

UploadModel = TrafficDataMetadata | OptimizationMetadata

# --- Endpoints ---

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/upload")
async def upload_metadata(metadata: UploadModel = Body(...)):
    try:
        # Upload JSON to IPFS
        cid = await upload_json_to_ipfs(metadata.dict())

        # Map type and timestamp
        data_type = DATA_TYPE_MAP[metadata.type]
        timestamp_unix = convert_to_unix_timestamp(metadata.timestamp)

        # Store reference in BlockDAG
        await store_metadata_in_blockdag(
            traffic_light_id=metadata.traffic_light_id,
            timestamp=timestamp_unix,
            data_type=data_type,
            cid=cid
        )

        # Insert metadata into the database
        query = insert(metadata_index).values({
            "type": metadata.type,
            "timestamp": datetime.fromisoformat(metadata.timestamp),
            "traffic_light_id": metadata.traffic_light_id
        })
        await database.execute(query)

        return {"message": "Metadata uploaded successfully", "cid": cid}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_metadata(
    traffic_light_id: str = Query(...),
    timestamp: str = Query(...),
    type: Literal["data", "optimization"] = Query(...)
):
    try:
        # Map type and timestamp
        data_type = DATA_TYPE_MAP[type]
        timestamp_unix = convert_to_unix_timestamp(timestamp)

        # Fetch CID from BlockDAG
        cid = await fetch_metadata_from_blockdag(
            traffic_light_id=traffic_light_id,
            timestamp=timestamp_unix,
            data_type=data_type
        )

        # Download JSON from IPFS
        data = await download_json_from_ipfs(cid)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/{num_pairs}")
async def upload_generated_pairs(num_pairs: int):
    if num_pairs <= 0:
        raise HTTPException(status_code=400, detail="num_pairs must be a positive integer.")

    try:
        # Generate the JSONs
        generate_jsons(num_pairs)

        uploaded = []

        # Upload all generated files
        for filepath in sorted(glob.glob(os.path.join(input_dir, "*.json")))[-2*num_pairs:]:
            with open(filepath, 'r') as f:
                metadata = json.load(f)

            # Upload JSON to IPFS
            cid = await upload_json_to_ipfs(metadata)

            # Map type and timestamp
            data_type = DATA_TYPE_MAP[metadata["type"]]
            timestamp_unix = convert_to_unix_timestamp(metadata["timestamp"])
            traffic_light_id = metadata["traffic_light_id"]

            # Store metadata in BlockDAG
            await store_metadata_in_blockdag(
                traffic_light_id=traffic_light_id,
                timestamp=timestamp_unix,
                data_type=data_type,
                cid=cid
            )
            
            uploaded.append({
                "file": os.path.basename(filepath),
                "cid": cid,
                "type": metadata["type"],
                "timestamp": datetime.fromisoformat(metadata["timestamp"]),
                "traffic_light_id": metadata["traffic_light_id"]
            })


        # Insert metadata into the database
        query = insert(metadata_index).values([
            {
                "type": metadata["type"],
                "timestamp": metadata["timestamp"],
                "traffic_light_id": metadata["traffic_light_id"]
            } for metadata in uploaded
        ])
        await database.execute(query)


        return {
            "message": f"Successfully uploaded {len(uploaded)} JSONs (data+optimization pairs).",
            "uploads": uploaded
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
