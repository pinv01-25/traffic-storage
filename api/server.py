from datetime import datetime
from fastapi import FastAPI, HTTPException, Body, Query
from pydantic import BaseModel
from typing import  Literal
import os
import glob
import json
from sqlalchemy import insert, select
from fastapi import Request
from api.modules.ipfs.ipfs_manager import upload_json_to_ipfs, download_json_from_ipfs
from api.modules.blockdag.blockdag_client import store_metadata_in_blockdag, fetch_metadata_from_blockdag
from api.scripts.generate_jsons import generate_jsons
import logging

# --- Logging configuration ---
logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG si necesitas más detalle
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("traffic_api")


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
    timestamp: int
    traffic_light_id: str
    controlled_edges: list[str]
    metrics: dict
    vehicle_stats: dict

class OptimizationMetadata(BaseModel):
    version: str = "1.0"
    type: Literal["optimization"]
    timestamp: int
    traffic_light_id: str
    optimization: dict
    impact: dict

class DownloadRequest(BaseModel):
    traffic_light_id: str
    timestamp: int
    type: Literal["data", "optimization"]

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

        # Store reference in BlockDAG
        await store_metadata_in_blockdag(
            traffic_light_id=metadata.traffic_light_id,
            timestamp=metadata.timestamp,
            data_type=data_type,
            cid=cid
        )

        logger.info(f"Uploaded metadata for traffic_light_id={metadata.traffic_light_id}, timestamp={metadata.timestamp}, cid={cid}")

        return {
            "message": "Metadata uploaded successfully",
            "cid": cid,
            "type": metadata.type,
            "timestamp": metadata.timestamp,
            "traffic_light_id": metadata.traffic_light_id
        }

    except Exception as e:
        logger.exception("Error uploading metadata")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
async def download_metadata(body: DownloadRequest):
    try:
        cid = await fetch_metadata_from_blockdag(
            traffic_light_id=body.traffic_light_id,
            timestamp=body.timestamp,
            data_type=DATA_TYPE_MAP[body.type]
        )

        data = await download_json_from_ipfs(cid)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    