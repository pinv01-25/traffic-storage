#!/usr/bin/env python3

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_csv(path: str, header: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)


def record_csv(path: str, row: list[Any]) -> None:
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def http_post_json(url: str, payload: Dict[str, Any], timeout: int) -> requests.Response:
    return requests.post(
        url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout
    )


def extract_field(container: Dict[str, Any], key: str) -> Optional[Any]:
    return container.get(key)


def do_upload(base_url: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/upload"
    t0 = time.perf_counter()
    start_iso = now_iso()
    resp = http_post_json(url, payload, timeout)
    end_iso = now_iso()
    t1 = time.perf_counter()
    elapsed_ms = int((t1 - t0) * 1000)
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        error = f"non-json-response: {exc}"
    return {
        "mode": "upload",
        "http_status": resp.status_code,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "elapsed_ms": elapsed_ms,
        "response": data,
        "error": error,
    }


def do_download(
    base_url: str, traffic_light_id: str, timestamp: int, data_type: str, timeout: int
) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/download"
    body = {
        "traffic_light_id": traffic_light_id,
        "timestamp": timestamp,
        "type": data_type,
    }
    t0 = time.perf_counter()
    start_iso = now_iso()
    resp = http_post_json(url, body, timeout)
    end_iso = now_iso()
    t1 = time.perf_counter()
    elapsed_ms = int((t1 - t0) * 1000)
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        error = f"non-json-response: {exc}"
    return {
        "mode": "download",
        "http_status": resp.status_code,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "elapsed_ms": elapsed_ms,
        "response": data,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark upload/download to traffic-storage (IPFS + BlockDAG)"
    )
    parser.add_argument(
        "--storage-url",
        default=os.environ.get("STORAGE_API_URL", "http://localhost:8000"),
        help="Base URL of traffic-storage API (default: http://localhost:8000)",
    )
    parser.add_argument("--input-json", help="Path to JSON payload to upload (unified 2.0)")
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of repetitions per mode (default: 5)"
    )
    parser.add_argument(
        "--timeout", type=int, default=60, help="HTTP timeout seconds (default: 60)"
    )
    parser.add_argument(
        "--output-csv", default="logs/storage_bench/results.csv", help="Path to CSV output (append)"
    )
    parser.add_argument(
        "--output-dir", default="logs/storage_bench", help="Directory to store JSON responses"
    )
    parser.add_argument(
        "--download-after-upload",
        action="store_true",
        help="Run download right after each upload using returned identifiers",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Skip upload and only run download using explicit identifiers",
    )
    parser.add_argument(
        "--tl-id", dest="traffic_light_id", help="traffic_light_id for download-only mode"
    )
    parser.add_argument("--timestamp", type=int, help="Unix timestamp for download-only mode")
    parser.add_argument(
        "--type",
        dest="data_type",
        choices=["data", "optimization"],
        help="Type for download-only mode",
    )

    args = parser.parse_args()

    header = [
        "run_id",
        "mode",
        "start_iso",
        "end_iso",
        "elapsed_ms",
        "http_status",
        "traffic_light_id",
        "timestamp",
        "type",
        "cid",
        "tx_hash",
        "response_path",
        "error",
    ]
    ensure_csv(args.output_csv, header)

    base_url = args.storage_url
    os.makedirs(args.output_dir, exist_ok=True)

    if args.download_only:
        if not (args.traffic_light_id and args.timestamp and args.data_type):
            print("--download-only requires --tl-id, --timestamp and --type", file=sys.stderr)
            return 2
        for i in range(args.runs):
            res = do_download(
                base_url, args.traffic_light_id, args.timestamp, args.data_type, args.timeout
            )
            resp = res["response"] or {}
            response_path = os.path.join(args.output_dir, f"download_{i + 1}.json")
            write_json(response_path, resp if isinstance(resp, dict) else {"raw": str(resp)})
            row = [
                i + 1,
                res["mode"],
                res["start_iso"],
                res["end_iso"],
                res["elapsed_ms"],
                res["http_status"],
                args.traffic_light_id,
                args.timestamp,
                args.data_type,
                extract_field(resp, "cid"),
                extract_field(resp, "tx_hash"),
                response_path,
                res["error"],
            ]
            record_csv(args.output_csv, row)
        return 0

    if not args.input_json:
        print("--input-json is required unless --download-only", file=sys.stderr)
        return 2

    payload = read_json(args.input_json)

    for i in range(args.runs):
        # Upload
        up = do_upload(base_url, payload, args.timeout)
        up_resp = up["response"] or {}
        up_path = os.path.join(args.output_dir, f"upload_{i + 1}.json")
        write_json(up_path, up_resp if isinstance(up_resp, dict) else {"raw": str(up_resp)})

        # Best-effort identifiers for download
        tl_id = extract_field(up_resp, "traffic_light_id") or extract_field(
            payload, "traffic_light_id"
        )
        ts = extract_field(up_resp, "timestamp") or extract_field(payload, "timestamp")
        dtype = extract_field(up_resp, "type") or extract_field(payload, "type")

        row_up = [
            i + 1,
            up["mode"],
            up["start_iso"],
            up["end_iso"],
            up["elapsed_ms"],
            up["http_status"],
            tl_id,
            ts,
            dtype,
            extract_field(up_resp, "cid"),
            extract_field(up_resp, "tx_hash"),
            up_path,
            up["error"],
        ]
        record_csv(args.output_csv, row_up)

        if args.download_after_upload and tl_id and ts and dtype:
            dn = do_download(base_url, str(tl_id), int(ts), str(dtype), args.timeout)
            dn_resp = dn["response"] or {}
            dn_path = os.path.join(args.output_dir, f"download_after_upload_{i + 1}.json")
            write_json(dn_path, dn_resp if isinstance(dn_resp, dict) else {"raw": str(dn_resp)})
            row_dn = [
                i + 1,
                dn["mode"],
                dn["start_iso"],
                dn["end_iso"],
                dn["elapsed_ms"],
                dn["http_status"],
                tl_id,
                ts,
                dtype,
                extract_field(dn_resp, "cid"),
                extract_field(dn_resp, "tx_hash"),
                dn_path,
                dn["error"],
            ]
            record_csv(args.output_csv, row_dn)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
