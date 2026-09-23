#!/usr/bin/env bash
# OpenClaw / 通用 agent 入口：包装 repro_pack.py。
# OpenClaw 会把 $OPENCLAW_HOME 注入 shell 环境（未注入的场合照常可用）。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/repro_pack.py" "$@"
