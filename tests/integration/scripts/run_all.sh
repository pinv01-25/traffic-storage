#!/usr/bin/env bash

set -euo pipefail

# Orchestrates storage metrics collection and precision verification
# across scenarios: bajo, medio, alto.
#
# Usage:
#   ./scripts/run_all.sh                 # defaults: 5 runs, localhost URLs
#   ./scripts/run_all.sh --runs 10 --storage-url http://localhost:8000
#   ./scripts/run_all.sh --payload-dir /path/to/payloads
#
# If --payload-dir is provided and contains <scenario>.json files
# (bajo.json, medio.json, alto.json), the metrics script will use them.
# Otherwise, it will generate a synthetic payload for each run.

RUNS=5
STORAGE_URL="http://localhost:8000"
SLEEP_BETWEEN=0.5
OUT_DIR="logs/storage_metrics"
PAYLOAD_DIR=""
SCENARIOS=("bajo" "medio" "alto")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runs)
      RUNS="$2"; shift 2 ;;
    --storage-url)
      STORAGE_URL="$2"; shift 2 ;;
    --sleep-between)
      SLEEP_BETWEEN="$2"; shift 2 ;;
    --out-dir)
      OUT_DIR="$2"; shift 2 ;;
    --payload-dir)
      PAYLOAD_DIR="$2"; shift 2 ;;
    --scenarios)
      IFS=',' read -r -a SCENARIOS <<< "$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

METRICS="$ROOT_DIR/scripts/storage_metrics.py"
VERIFY="$ROOT_DIR/scripts/verify_storage_precision.py"

chmod +x "$METRICS" "$VERIFY" || true

echo "Running storage metrics..."
for SC in "${SCENARIOS[@]}"; do
  echo "== Scenario: $SC =="
  if [[ -n "$PAYLOAD_DIR" && -f "$PAYLOAD_DIR/$SC.json" ]]; then
    "$METRICS" --scenario "$SC" --runs "$RUNS" --payload "$PAYLOAD_DIR/$SC.json" \
      --storage-url "$STORAGE_URL" --sleep-between "$SLEEP_BETWEEN" --out-dir "$OUT_DIR"
  else
    "$METRICS" --scenario "$SC" --runs "$RUNS" \
      --storage-url "$STORAGE_URL" --sleep-between "$SLEEP_BETWEEN" --out-dir "$OUT_DIR"
  fi
done

echo "\nVerifying precision..."
for SC in "${SCENARIOS[@]}"; do
  "$VERIFY" --scenario "$SC" --base-dir "$OUT_DIR"
done

echo "\nAll done. Outputs in: $OUT_DIR"


