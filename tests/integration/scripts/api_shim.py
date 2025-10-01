#!/usr/bin/env python3
"""
API shim for SUMO Helper frontend compatibility.

Exposes /api/* endpoints expected by the frontend and forwards to the
backend (default http://localhost:8000), transforming payloads as needed.

Fixes:
 - POST /api/maps/select-area: accepts {bbox:{minLat,minLon,maxLat,maxLon}}
   and forwards body as {north,south,east,west,place_name?}.
 - Proxies other /api/* calls by stripping the /api prefix and forwarding.

Run:
  ./scripts/api_shim.py --listen 127.0.0.1:8001 --backend http://localhost:8000

Then point the frontend API base to http://localhost:8001
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import httpx


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--listen", default="127.0.0.1:8001", help="host:port to listen on")
    p.add_argument("--backend", default="http://localhost:8000", help="Backend base URL")
    return p.parse_args()


def create_app(backend_base: str) -> FastAPI:
    app = FastAPI(title="SUMO Helper API Shim", version="1.0.0")

    @app.post("/api/maps/select-area")
    async def select_area(req: Request):
        try:
            body = await req.json()
        except Exception:
            return JSONResponse({"detail": "Invalid JSON"}, status_code=400)

        new_body: Dict[str, Any]
        if isinstance(body, dict) and "bbox" in body:
            bbox = body.get("bbox", {}) or {}
            try:
                new_body = {
                    "north": float(bbox["maxLat"]),
                    "south": float(bbox["minLat"]),
                    "east": float(bbox["maxLon"]),
                    "west": float(bbox["minLon"]),
                }
            except Exception:
                return JSONResponse({"detail": "bbox requires minLat,minLon,maxLat,maxLon"}, status_code=422)
            if "place_name" in body:
                new_body["place_name"] = body["place_name"]
        else:
            new_body = body

        url = f"{backend_base}/api/maps/select-area"
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=new_body)
        return JSONResponse(r.json(), status_code=r.status_code)

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_generic(req: Request, path: str):
        # Strip /api and forward
        fwd_url = f"{backend_base}/{path}"
        method = req.method
        headers = dict(req.headers)
        # Remove host-related headers to avoid issues
        headers.pop("host", None)
        try:
            content = await req.body()
            # Try to keep JSON if possible
            if headers.get("content-type", "").startswith("application/json") and content:
                data = json.loads(content.decode("utf-8"))
            else:
                data = None
        except Exception:
            data = None

        async with httpx.AsyncClient(timeout=120.0) as client:
            if method == "GET":
                r = await client.get(fwd_url, params=dict(req.query_params), headers=headers)
            else:
                if data is not None:
                    r = await client.request(method, fwd_url, json=data, params=dict(req.query_params), headers=headers)
                else:
                    r = await client.request(method, fwd_url, content=content, params=dict(req.query_params), headers=headers)

        return Response(content=r.content, status_code=r.status_code, headers={"content-type": r.headers.get("content-type", "application/json")})

    return app


def main() -> None:
    args = parse_args()
    host, port_s = args.listen.split(":")
    app = create_app(args.backend)
    uvicorn.run(app, host=host, port=int(port_s), log_level="info")


if __name__ == "__main__":
    main()


