#!/usr/bin/env bash
set -euo pipefail

curl -sS "http://127.0.0.1:3000/health" >/dev/null 2>&1 || true

# 通过 OpenClaw 当前会话给用户发提醒
# 如果 openclaw CLI 不可用，这个脚本只作为占位，提醒逻辑仍可人工兜底。
if command -v openclaw >/dev/null 2>&1; then
  openclaw message send --channel telegram --target telegram:7658698483 --message "请发今天的 51吃瓜 CSV，我这边收到后会顺手把 51福利导航 一起更新。" >/dev/null 2>&1 || true
fi
