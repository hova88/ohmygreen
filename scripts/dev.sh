#!/usr/bin/env bash
set -euo pipefail

python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

cleanup() {
  kill $API_PID || true
}
trap cleanup EXIT

cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
