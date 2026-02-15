#!/bin/bash
# Optional: run ON the Arduino UNO Q (via SSH) to install deps.
# With FER+ ONNX, requirements.txt uses only opencv-python-headless (no libGL).
# App Lab usually installs automatically; use this if packages are missing.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$SCRIPT_DIR")"
REQ="$APP_ROOT/python/requirements.txt"

echo "Emotion Poet - Device setup"
pip install -r "$REQ"
echo "Done. Restart the app."
