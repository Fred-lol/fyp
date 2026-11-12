#!/usr/bin/env bash
# Start the public AquaLoad service and its private tracking API together.
# The API remains internal to the service; visitors use only the HTTPS app URL.
set -euo pipefail

export AQUALOAD_TRACKING_API="http://127.0.0.1:8000"
export AQUALOAD_MANAGED_TRACKING_API="1"

python -m uvicorn tracking_api:app --host 127.0.0.1 --port 8000 &
tracking_pid=$!

cleanup() {
  kill "$tracking_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait briefly for FastAPI to finish its schema check before Streamlit serves
# the tracking pages. This removes a first-load race condition.
for _ in $(seq 1 30); do
  if python -c "import socket; s=socket.create_connection(('127.0.0.1', 8000), .2); s.close()" 2>/dev/null; then
    break
  fi
  sleep 0.1
done

exec streamlit run homepage.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT:-8501}" \
  --server.headless true
