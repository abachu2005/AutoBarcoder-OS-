#!/usr/bin/env bash
# Convenience launcher: creates a venv on first run, then starts the web UI.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON=${PYTHON:-python3}

if [ ! -d .venv ]; then
  echo "Creating virtualenv in .venv …"
  "$PYTHON" -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
  ./.venv/bin/pip install -r webapp/requirements.txt
fi

echo "Open http://127.0.0.1:8000 in your browser."
exec ./.venv/bin/python -m uvicorn webapp.backend.main:app --host 127.0.0.1 --port 8000 "$@"
