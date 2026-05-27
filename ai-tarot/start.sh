#!/bin/bash
cd "$(dirname "$0")"
set -a
source .env 2>/dev/null
set +a
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 18899 "$@"
