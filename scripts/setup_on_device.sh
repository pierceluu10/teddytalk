#!/bin/bash
# Run ON the Arduino UNO Q (via SSH) to install deps from bundle.
# Use bundle from scripts/bundle_all.py - copy python/bundle/ to device first.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$SCRIPT_DIR")"
REQ="$APP_ROOT/python/requirements.txt"
BUNDLE="$APP_ROOT/python/bundle/wheels"

echo "Teddy Talk - Device setup"
if [ -d "$BUNDLE" ]; then
    echo "Installing from offline bundle..."
    pip install --no-index --find-links "$BUNDLE" -r "$REQ"
else
    echo "No bundle found. Installing from internet..."
    pip install -r "$REQ"
fi
echo "Done. Restart the app."
