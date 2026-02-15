"""
FER+ ONNX emotion recognizer (lightweight, no libGL).
Uses opencv-python-headless + onnxruntime only.
Model: emotion-ferplus-12-int8.onnx (~19 MB) from ONNX Model Zoo.
"""
import os
import numpy as np

_BUNDLED_MODELS = os.path.join(os.path.dirname(__file__), "models")
# Use fp32 model for better accuracy (int8 often biased to neutral)
_MODEL_NAME = "emotion-ferplus-8"
_LABELS = ["neutral", "happiness", "surprise", "sadness", "anger", "disgust", "fear", "contempt"]


def _get_model_path():
    """Use bundled model if present, else download to ~/.emotion_ferplus."""
    bundled = os.path.join(_BUNDLED_MODELS, _MODEL_NAME + ".onnx")
    if os.path.isfile(bundled):
        return bundled
    cache_dir = os.path.join(os.path.expanduser("~"), ".emotion_ferplus")
    os.makedirs(cache_dir, exist_ok=True)
    fpath = os.path.join(cache_dir, _MODEL_NAME + ".onnx")
    if not os.path.isfile(fpath):
        import urllib.request
        url = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx"
        print("Downloading FER+ model from", url)
        urllib.request.urlretrieve(url, fpath)
    return fpath


def load_emotion_recognizer(model_name=None):
    """
    Load FER+ ONNX recognizer. model_name is ignored (kept for API compat).
    Returns an object with predict_emotions(face_rgb, logits=False) -> (emotion, scores).
    """
    import onnxruntime as ort

    path = _get_model_path()
    session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])

    class FERPlusRecognizer:
        def predict_emotions(self, face_rgb, logits=False):
            """face_rgb: numpy array (H,W,3) RGB. Returns (emotion_str, scores_array)."""
            import cv2
            gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
                gray = clahe.apply(gray)
            except Exception:
                pass
            resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_LINEAR)
            # FER+ expects float32 in [0, 255] (per ONNX Model Zoo)
            inp = resized.astype(np.float32)
            inp = np.expand_dims(np.expand_dims(inp, 0), 0)
            out = session.run(None, {"Input3": inp})[0]
            scores = np.squeeze(out)
            if not logits:
                exp = np.exp(scores - np.max(scores))
                scores = exp / exp.sum()
            idx = int(np.argmax(scores))
            top_emotion = _LABELS[idx]
            top_score = float(scores[idx])
            # If top is neutral but a strong expression has decent confidence, prefer it
            strong = ["happiness", "anger", "surprise", "sadness", "fear"]
            if top_emotion == "neutral" and top_score < 0.90:
                best_strong = None
                best_score = 0.0
                for i, lab in enumerate(_LABELS):
                    s = float(scores[i])
                    if lab in strong and s > 0.15 and s > best_score:
                        best_strong, best_score = lab, s
                if best_strong is not None:
                    return best_strong, scores
            return top_emotion, scores

    return FERPlusRecognizer()
