#!/bin/bash
set -euo pipefail

cd /home/kawaii_ai_office/e-midi

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/python -m ensurepip --upgrade
fi

./.venv/bin/pip install -r server/requirements.txt
PYTHONPATH=/home/kawaii_ai_office/e-midi ./.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8765 &
echo "E-MIDI Server started on ws://localhost:8765"
echo "Open http://localhost:8765/ in browser"
