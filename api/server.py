from fastapi import FastAPI, HTTPException
from api.modules.ipfs.ipfs_manager import upload_json_to_ipfs, download_json_from_ipfs
from api.modules.blockdag.blockdag_client import store_metadata_in_blockdag, fetch_metadata_from_blockdag
from api.schemas.traffic_data import TrafficData
from api.schemas.optimization_data import OptimizationData
from pydantic import BaseModel

app = FastAPI(title="Traffic Storage API", version="1.0")

# Models for input
class StoreRequest(BaseModel):
    type: str  # "data" or "optimization"
    payload: dict  # Actual traffic or optimization JSON

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/store")
async def store_data(req: StoreRequest):
    try:
        cid = await upload_json_to_ipfs(req.payload)
        await store_metadata_in_blockdag(req.type, req.payload["timestamp"], req.payload["traffic_light_id"], cid)
        return {"message": "Data stored successfully", "cid": cid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fetch")
async def fetch_data(traffic_light_id: str, timestamp: str):
    try:
        cid = await fetch_metadata_from_blockdag(traffic_light_id, timestamp)
        data = await download_json_from_ipfs(cid)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
