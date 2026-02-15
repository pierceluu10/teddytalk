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

# 2. Optional: pip download for offline (UNO Q is aarch64/arm64 Linux)
REQUIREMENTS="$APP_ROOT/python/requirements.txt"
WHEELS_DIR="$APP_ROOT/python/wheels"
if [ -f "$REQUIREMENTS" ]; then
    echo "[2/2] Downloading Python wheels for offline install..."
    mkdir -p "$WHEELS_DIR"
    pip download -r "$REQUIREMENTS" -d "$WHEELS_DIR" \
        --platform manylinux2014_aarch64 --python-version 3.11 --only-binary=:all: 2>/dev/null || true
fi

echo ""
echo "Setup complete. Copy the teddytalk folder to your UNO Q."
