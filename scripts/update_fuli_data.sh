#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-ga4"
PYTHON_BIN="$VENV_DIR/bin/python"
SERVICE_ACCOUNT_JSON="${GA4_SERVICE_ACCOUNT_JSON:-/root/.openclaw/media/inbound/ga-auto-report-490102-fae850a52446---4e6497d7-3f1e-45e8-8ab2-05178654fdfe.json}"
PROPERTY_ID="${GA4_PROPERTY_ID:-361679028}"
START_DATE="${GA4_START_DATE:-2026-02-28}"
END_DATE="${GA4_END_DATE:-$(date +%F)}"
OUTPUT_JSON="${GA4_OUTPUT_JSON:-$ROOT_DIR/fuli-ga4.json}"
RETENTION_MODE="${GA4_RETENTION_MODE:-cohort-active-users}"

if [[ ! -f "$SERVICE_ACCOUNT_JSON" ]]; then
  echo "[ERROR] service account JSON not found: $SERVICE_ACCOUNT_JSON" >&2
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "[INFO] creating venv: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install google-auth requests >/dev/null
fi

echo "[INFO] updating 51福利导航 data..."
echo "[INFO] property_id=$PROPERTY_ID start_date=$START_DATE end_date=$END_DATE retention_mode=$RETENTION_MODE"

"$PYTHON_BIN" "$ROOT_DIR/scripts/ga4_fuli_report.py" \
  --property-id "$PROPERTY_ID" \
  --service-account-json "$SERVICE_ACCOUNT_JSON" \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --retention-mode "$RETENTION_MODE" \
  --output "$OUTPUT_JSON" \
  --pretty

echo "[OK] wrote: $OUTPUT_JSON"
