#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_CSV="${CHIGUA_INPUT_CSV:-$ROOT_DIR/data/chigua-latest.csv}"
OUTPUT_JSON="${CHIGUA_OUTPUT_JSON:-$ROOT_DIR/chigua-data.json}"

if [[ ! -f "$INPUT_CSV" ]]; then
  echo "[ERROR] CSV not found: $INPUT_CSV" >&2
  exit 1
fi

echo "[INFO] converting 51吃瓜 CSV -> JSON"
echo "[INFO] input=$INPUT_CSV"
echo "[INFO] output=$OUTPUT_JSON"

python3 "$ROOT_DIR/scripts/chigua_csv_to_json.py" \
  --input "$INPUT_CSV" \
  --output "$OUTPUT_JSON" \
  --pretty

echo "[OK] wrote: $OUTPUT_JSON"
