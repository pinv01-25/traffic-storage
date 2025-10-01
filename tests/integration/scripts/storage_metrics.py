#!/usr/bin/env python3
"""
Storage metrics collector for traffic-storage API.

Measures upload and download latencies and records results (CSV + JSON files)
for reproducible evidence in the Sept (2°) report.

Usage examples:
  - Default synthetic payload, 5 runs, local storage URL:
      ./scripts/storage_metrics.py --scenario bajo

  - Custom payload file and 10 runs:
      ./scripts/storage_metrics.py --scenario alto --runs 10 --payload /path/to/payload.json

  - Custom storage URL:
      ./scripts/storage_metrics.py --scenario medio --storage-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure traffic-storage upload/download metrics")
    parser.add_argument("--scenario", required=True, help="Scenario label: bajo | medio | alto | custom")
    parser.add_argument("--runs", type=int, default=5, help="Number of repetitions per execution (default: 5)")
    parser.add_argument("--payload", type=str, default="", help="Path to JSON payload file (data format 2.0). If omitted, a synthetic payload is generated")
    parser.add_argument("--storage-url", type=str, default="http://localhost:8000", help="Base URL of traffic-storage API")
    parser.add_argument("--sleep-between", type=float, default=0.5, help="Seconds to sleep between ops to avoid bursts (default: 0.5s)")
    parser.add_argument("--out-dir", type=str, default="logs/storage_metrics", help="Output directory for CSV and JSON evidence")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def http_post_json(url: str, payload: Dict[str, Any], timeout: float = 60.0) -> Tuple[int, Dict[str, Any], float]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.perf_counter() - start
            status = resp.getcode()
            raw = resp.read()
            data = json.loads(raw.decode("utf-8")) if raw else {}
            return status, data, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        raw = e.read()
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {"error": str(e)}
        except Exception:
            data = {"error": str(e), "body": raw.decode("utf-8", errors="ignore")}
        return e.code, data, elapsed
    except urllib.error.URLError as e:
        elapsed = time.perf_counter() - start
        return 0, {"error": str(e)}, elapsed


def make_synthetic_payload() -> Dict[str, Any]:
    # Minimal valid data payload (unified 2.0 format expected by traffic-storage)
    ts_unix = int(time.time())
    return {
        "version": "2.0",
        "type": "data",
        "timestamp": ts_unix,
        "traffic_light_id": "21",
        "sensors": [
            {
                "traffic_light_id": "21",
                "controlled_edges": ["edge42", "edge43"],
                "metrics": {
                    "vehicles_per_minute": 40,
                    "avg_speed_kmh": 30.0,
                    "avg_circulation_time_sec": 25.0,
                    "density": 0.50,
                },
                "vehicle_stats": {"motorcycle": 5, "car": 30, "bus": 1, "truck": 2},
            }
        ],
    }


def extract_download_request_from_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return {
            "traffic_light_id": payload["traffic_light_id"],
            "timestamp": payload["timestamp"],
            "type": payload.get("type", "data"),
        }
    except KeyError:
        return None


def open_csv_writer(csv_path: str) -> Tuple[csv.writer, Any]:
    exists = os.path.exists(csv_path)
    f = open(csv_path, "a", newline="", encoding="utf-8")
    writer = csv.writer(f)
    if not exists:
        writer.writerow([
            "datetime_utc",
            "scenario",
            "run_index",
            "operation",
            "elapsed_s",
            "status",
            "storage_url",
            "cid",
            "traffic_light_id",
            "timestamp",
            "type",
        ])
    return writer, f


def main() -> int:
    args = parse_args()

    base_out = os.path.abspath(args.out_dir)
    ensure_dir(base_out)
    scenario_dir = os.path.join(base_out, args.scenario)
    ensure_dir(scenario_dir)

    csv_path = os.path.join(base_out, "storage_metrics.csv")
    writer, csv_file = open_csv_writer(csv_path)

    try:
        if args.payload:
            payload = read_json_file(args.payload)
        else:
            payload = make_synthetic_payload()

        download_req = extract_download_request_from_payload(payload)
        if download_req is None:
            print("[ERROR] Payload missing required fields for download request (traffic_light_id, timestamp)", file=sys.stderr)
            return 2

        upload_url = args.storage_url.rstrip("/") + "/upload/"
        download_url = args.storage_url.rstrip("/") + "/download/"

        for i in range(args.runs):
            run_tag = f"run_{i+1:02d}"
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            # Upload
            status_u, resp_u, elapsed_u = http_post_json(upload_url, payload)
            cid = resp_u.get("cid") if isinstance(resp_u, dict) else None

            up_json_path = os.path.join(scenario_dir, f"{stamp}_{run_tag}_upload.json")
            write_json_file(up_json_path, {"request": payload, "response": resp_u, "status": status_u, "elapsed_s": elapsed_u})

            writer.writerow([
                now_iso(),
                args.scenario,
                i + 1,
                "upload",
                f"{elapsed_u:.6f}",
                status_u,
                args.storage_url,
                cid or "",
                payload.get("traffic_light_id", ""),
                payload.get("timestamp", ""),
                payload.get("type", ""),
            ])
            csv_file.flush()

            time.sleep(args.sleep_between)

            # Download
            status_d, resp_d, elapsed_d = http_post_json(download_url, download_req)

            down_json_path = os.path.join(scenario_dir, f"{stamp}_{run_tag}_download.json")
            write_json_file(down_json_path, {"request": download_req, "response": resp_d, "status": status_d, "elapsed_s": elapsed_d})

            writer.writerow([
                now_iso(),
                args.scenario,
                i + 1,
                "download",
                f"{elapsed_d:.6f}",
                status_d,
                args.storage_url,
                cid or resp_d.get("cid", "") if isinstance(resp_d, dict) else "",
                download_req.get("traffic_light_id", ""),
                download_req.get("timestamp", ""),
                download_req.get("type", ""),
            ])
            csv_file.flush()

            time.sleep(args.sleep_between)

        print(f"Done. CSV: {csv_path}\nJSON: {scenario_dir}")
        return 0
    finally:
        try:
            csv_file.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())


