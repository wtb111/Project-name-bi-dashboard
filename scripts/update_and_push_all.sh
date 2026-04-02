#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# 1) 51吃瓜（如果源 CSV 存在就更新）
if [[ -f "$ROOT_DIR/data/chigua-latest.csv" ]]; then
  bash "$ROOT_DIR/scripts/update_chigua_data.sh"
else
  echo "[WARN] skip chigua: data/chigua-latest.csv not found"
fi

# 2) 51福利导航
bash "$ROOT_DIR/scripts/update_fuli_data.sh"

# 3) 提交并推送到 GitHub
if ! git diff --quiet -- chigua-data.json fuli-ga4.json dashboard-dual-csv.html index.html 2>/dev/null; then
  git add chigua-data.json fuli-ga4.json dashboard-dual-csv.html 2>/dev/null || true
  git add index.html 2>/dev/null || true
  git commit -m "Auto-update dashboard data $(date '+%F %T')" || true
  git push origin main
  echo "[OK] pushed latest dashboard data to GitHub"
else
  echo "[INFO] no tracked dashboard changes to commit"
fi
