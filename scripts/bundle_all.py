#!/usr/bin/env python3
"""
Bundle everything for offline deploy: FER+ model + all Python deps.
Run once on a machine with internet. Copy python/bundle/ to UNO Q.
On device: pip install --no-index --find-links python/bundle/wheels -r python/requirements.txt
"""
import os
import subprocess
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(SCRIPT_DIR)
BUNDLE_DIR = os.path.join(APP_ROOT, "python", "bundle")
WHEELS_DIR = os.path.join(BUNDLE_DIR, "wheels")
MODELS_DIR = os.path.join(APP_ROOT, "python", "models")

# UNO Q is aarch64 Linux
PLATFORM = "manylinux2014_aarch64"
PYTHON_VERSION = "3.11"


def download_model():
    """Download FER+ ONNX model."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_url = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
    model_path = os.path.join(MODELS_DIR, "emotion-ferplus-8.onnx")
    if os.path.isfile(model_path):
        print(f"  Model exists: {model_path}")
        return True
    print(f"  Downloading FER+ model (~34 MB)...")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        print(f"  Saved to {model_path}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def download_wheels():
    """Download all pip deps for aarch64."""
    os.makedirs(WHEELS_DIR, exist_ok=True)
    req = os.path.join(APP_ROOT, "python", "requirements.txt")
    if not os.path.isfile(req):
        print("  No requirements.txt")
        return False
    print(f"  Downloading wheels for {PLATFORM} Python {PYTHON_VERSION}...")
    cmd = [
        sys.executable, "-m", "pip", "download",
        "-r", req,
        "-d", WHEELS_DIR,
        "--platform", PLATFORM,
        "--python-version", PYTHON_VERSION,
        "--no-cache-dir",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  pip download failed: {r.stderr[:500] if r.stderr else r.stdout[:500]}")
        return False
    count = len([f for f in os.listdir(WHEELS_DIR) if f.endswith((".whl", ".tar.gz"))])
    print(f"  Downloaded {count} packages to {WHEELS_DIR}")
    return True


def main():
    print("Teddy Talk - Full offline bundle")
    print("=" * 50)
    print("[1/2] Models")
    if not download_model():
        sys.exit(1)
    print("[2/2] Python wheels")
    if not download_wheels():
        sys.exit(1)
    print("")
    print("Bundle complete. Contents:")
    print(f"  - {MODELS_DIR}")
    print(f"  - {WHEELS_DIR}")
    print("")
    print("On UNO Q, install from bundle:")
    print("  pip install --no-index --find-links python/bundle/wheels -r python/requirements.txt")
    print("")


if __name__ == "__main__":
    main()
