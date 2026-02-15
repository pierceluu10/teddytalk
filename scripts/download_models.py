#!/usr/bin/env python3
"""
Pre-download FER+ ONNX model for offline use on Arduino UNO Q.
Run this on a machine with internet before deploying to the device.
"""
import os
import sys
import urllib.request

# FER+ fp32 (~34 MB) - better accuracy than int8
MODEL_NAME = "emotion-ferplus-8"
MODEL_URL = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.dirname(script_dir)
    models_dir = os.path.join(app_root, "python", "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, f"{MODEL_NAME}.onnx")

    if os.path.isfile(model_path):
        print(f"Model already exists: {model_path}")
        return 0

    print(f"Downloading {MODEL_NAME} from {MODEL_URL}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, model_path)
        print(f"Saved to {model_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
