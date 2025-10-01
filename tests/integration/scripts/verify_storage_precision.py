#!/usr/bin/env python3
"""
Verify precision of storage round-trips by comparing uploaded JSON vs downloaded JSON.

Scans logs produced by scripts/storage_metrics.py and generates per-scenario
precision CSVs plus a small summary printed to stdout.

Usage examples:
  ./scripts/verify_storage_precision.py --scenario bajo
  ./scripts/verify_storage_precision.py --scenario alto --base-dir logs/storage_metrics
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify storage precision for a given scenario")
    parser.add_argument("--scenario", required=True, help="Scenario label: bajo | medio | alto | custom")
    parser.add_argument("--base-dir", default="logs/storage_metrics", help="Base directory where metrics logs were stored")
    parser.add_argument("--out-file", default="", help="Optional explicit output CSV path; defaults to <base-dir>/precision_<scenario>.csv")
    return parser.parse_args()


def sha256_sorted_json(data: Dict[str, Any]) -> str:
    # Deterministic hash of JSON by sorting keys
    s = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_run_pairs(scenario_dir: str) -> List[Tuple[str, str]]:
    # Expect files like: <stamp>_run_XX_upload.json and <stamp>_run_XX_download.json
    upload_files = sorted(glob.glob(os.path.join(scenario_dir, "*_run_*_upload.json")))
    pairs: List[Tuple[str, str]] = []
    for up in upload_files:
        down = up.replace("_upload.json", "_download.json")
        if os.path.exists(down):
            pairs.append((up, down))
    return pairs


def compare_round_trip(upload_json: Dict[str, Any], download_json: Dict[str, Any]) -> Tuple[bool, str, str]:
    # upload stored as { request: <payload>, response: ..., ... }
    # download stored as { request: {...}, response: <payload>, ... }
    up_payload = upload_json.get("request")
    down_payload = download_json.get("response")
    if not isinstance(up_payload, dict) or not isinstance(down_payload, dict):
        return False, "", ""
    up_hash = sha256_sorted_json(up_payload)
    down_hash = sha256_sorted_json(down_payload)
    return up_hash == down_hash, up_hash, down_hash


def open_csv_writer(path: str):
    exists = os.path.exists(path)
    f = open(path, "a", newline="", encoding="utf-8")
    writer = csv.writer(f)
    if not exists:
        writer.writerow([
            "scenario",
            "stamp_run",
            "precision_equal",
            "upload_sha256",
            "download_sha256",
            "upload_status",
            "download_status",
            "upload_elapsed_s",
            "download_elapsed_s",
            "cid",
        ])
    return writer, f


def main() -> int:
    args = parse_args()
    scenario_dir = os.path.join(args.base_dir, args.scenario)
    if not os.path.isdir(scenario_dir):
        print(f"No scenario directory found: {scenario_dir}")
        return 2

    out_file = args.out_file or os.path.join(args.base_dir, f"precision_{args.scenario}.csv")
    writer, f = open_csv_writer(out_file)

    try:
        pairs = find_run_pairs(scenario_dir)
        total = 0
        equal = 0
        for up_path, down_path in pairs:
            total += 1
            up = load_json(up_path)
            down = load_json(down_path)
            is_equal, up_hash, down_hash = compare_round_trip(up, down)
            if is_equal:
                equal += 1

            # derive stamp_run from file name
            stamp_run = os.path.basename(up_path).replace("_upload.json", "")
            cid = ""
            try:
                cid = (up.get("response") or {}).get("cid", "")
            except Exception:
                cid = ""

            writer.writerow([
                args.scenario,
                stamp_run,
                int(is_equal),
                up_hash,
                down_hash,
                up.get("status", ""),
                down.get("status", ""),
                up.get("elapsed_s", ""),
                down.get("elapsed_s", ""),
                cid,
            ])

        f.flush()
        pct = (equal / total * 100.0) if total else 0.0
        print(f"Scenario: {args.scenario} | pairs: {total} | exact matches: {equal} ({pct:.2f}%)\nCSV: {out_file}")
        return 0
    finally:
        try:
            f.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())


