#!/bin/bash
# Teddy Talk - Pre-download setup for Linux/macOS
# Run this before deploying to Arduino UNO Q

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Teddy Talk - Pre-download setup"
echo "App root: $APP_ROOT"
echo ""

# 1. Download FER+ model
echo "[1/2] Downloading FER+ ONNX model..."
python3 "$SCRIPT_DIR/download_models.py"

# 2. Bundle all Python deps for offline install
if [ -f "$APP_ROOT/python/requirements.txt" ]; then
    echo "[2/2] Bundling Python wheels for offline install..."
    python3 "$SCRIPT_DIR/bundle_all.py" || true
fi

echo ""
echo "Setup complete. Copy the teddytalk folder to your UNO Q."
