#!/usr/bin/env python3
"""
Teddy Talk - Arduino UNO Q
Face emotion detection, Gemini poem, ElevenLabs romantic TTS.
2x 16x4 LCD robot eyes, full Bluetooth speaker support, USB camera stream.
"""
# Suppress onnxruntime GPU discovery warning (UNO Q has no GPU)
import os
import sys
import shutil
import subprocess
os.environ.setdefault("ORT_DISABLE_GPU", "1")

# Bootstrap: install deps if missing (App Lab container may not have run pip)
def _bootstrap_deps():
    missing = []
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        missing.append("onnxruntime")
    try:
        from google import genai  # noqa: F401
    except ImportError:
        missing.append("google-genai")
    try:
        import elevenlabs  # noqa: F401
    except ImportError:
        missing.append("elevenlabs")
    if not missing:
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    req = os.path.join(script_dir, "requirements.txt")
    if not os.path.isfile(req):
        return
    print("Installing missing packages:", ", ".join(missing))
    pip = shutil.which("uv") or shutil.which("pip") or shutil.which("pip3") or "pip"
    if "uv" in pip:
        cmd = [pip, "pip", "install", "-r", req]
    else:
        cmd = [pip, "install", "-r", req]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        print("Packages installed. Restart the app.")
    else:
        print("Install failed:", r.stderr or r.stdout)
    sys.exit(0 if r.returncode == 0 else 1)

try:
    _bootstrap_deps()
except Exception as e:
    print(f"Bootstrap check failed: {e}")

from dotenv import load_dotenv

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
load_dotenv(os.path.join(_project_root, ".env"))

from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
import base64
import numpy as np
import io
import json
import threading
import time
from datetime import datetime, UTC

# --- Web UI ---
ui = WebUI()

# --- OpenCV (required for camera, used by emotion too) ---
cv2 = None
try:
    import cv2
except Exception as e:
    print(f"OpenCV not available: {e}")

# --- Emotion detection (FER+ ONNX, lightweight, no libGL) ---
EMOTION_AVAILABLE = False
face_cascade = None
emotion_recognizer = None
if cv2:
    try:
        from emotion_loader import load_emotion_recognizer
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        emotion_recognizer = load_emotion_recognizer()
        EMOTION_AVAILABLE = True
    except Exception as e:
        err = str(e)
        print(f"Emotion detection not available: {e}")
        _req = os.path.join(_script_dir, "requirements.txt")
        print(f"  -> Install deps: pip install -r {_req}")

# --- API keys (from .env) ---
def _load_api_key(env_var: str) -> str:
    return (os.environ.get(env_var) or "").strip()

GEMINI_KEY = _load_api_key("GEMINI_API_KEY")
ELEVENLABS_KEY = _load_api_key("ELEVENLABS_API_KEY")

# --- Gemini ---
gemini_client = None
if GEMINI_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"Gemini init failed: {e}")

# --- ElevenLabs ---
elevenlabs_client = None
if ELEVENLABS_KEY:
    try:
        from elevenlabs.client import ElevenLabs
        elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_KEY)
    except Exception as e:
        print(f"ElevenLabs init failed: {e}")

# --- Bluetooth & Audio ---
SELECTED_SINK = None  # PulseAudio sink name for playback

def _get_audio_env():
    env = os.environ.copy()
    for path in [
        (os.environ.get("XDG_RUNTIME_DIR") or "") + "/pulse/native",
        "/run/user/1000/pulse/native",
    ]:
        if path and os.path.exists(path):
            env["PULSE_SERVER"] = f"unix:{path}"
            break
    return env

def list_audio_sinks():
    """List PulseAudio sinks (includes Bluetooth when connected)."""
    if not shutil.which("pactl"):
        return []
    try:
        out = subprocess.run(
            ["pactl", "list", "sinks"],
            capture_output=True, text=True, timeout=5, env=_get_audio_env()
        )
        sinks = []
        current = {}
        for line in out.stdout.split("\n"):
            line = line.strip()
            if line.startswith("Sink #"):
                if current.get("name"):
                    sinks.append({"index": current.get("index", ""), "name": current["name"], "description": current.get("description", current["name"])})
                current = {"index": line.replace("Sink #", "").strip()}
            elif line.startswith("Name:"):
                current["name"] = line.split("Name:")[1].strip()
            elif line.startswith("Description:"):
                current["description"] = line.split("Description:")[1].strip()
        if current.get("name"):
            sinks.append({"index": current.get("index", ""), "name": current["name"], "description": current.get("description", current["name"])})
        return sinks
    except Exception as e:
        print(f"list_audio_sinks: {e}")
        return []

def bluetooth_scan():
    """Scan for Bluetooth devices (run bluetoothctl scan for a few seconds)."""
    if not shutil.which("bluetoothctl"):
        ui.send_message("bt_devices", {"devices": [], "error": "bluetoothctl not available"})
        return
    try:
        proc = subprocess.Popen(
            ["bluetoothctl", "scan", "on"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(8)
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        pass
    return bluetooth_devices()

def bluetooth_devices():
    """List known Bluetooth devices."""
    if not shutil.which("bluetoothctl"):
        return []
    try:
        out = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=10
        )
        devices = []
        for line in out.stdout.strip().split("\n"):
            if "Device" in line:
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2] if len(parts) > 2 else mac
                    devices.append({"mac": mac, "name": name})
        return devices
    except Exception as e:
        print(f"bluetooth_devices: {e}")
        return []

def bluetooth_pair(mac: str) -> dict:
    """Pair with a Bluetooth device."""
    try:
        subprocess.run(
            ["bluetoothctl", "trust", mac],
            capture_output=True, timeout=5
        )
        r = subprocess.run(
            ["bluetoothctl", "pair", mac],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0 and "Already exists" not in r.stderr:
            return {"ok": False, "error": r.stderr or r.stdout}
        subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=5)
        return {"ok": True}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Pairing timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def bluetooth_connect(mac: str) -> dict:
    """Connect to a paired Bluetooth device."""
    try:
        r = subprocess.run(
            ["bluetoothctl", "connect", mac],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr or r.stdout}
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _play_audio(filepath: str) -> bool:
    env = _get_audio_env()
    cmd = ["paplay", filepath]
    if SELECTED_SINK:
        cmd = ["paplay", "-d", SELECTED_SINK, filepath]
    for c in [cmd, ["mpv", "--no-video", "-q", filepath], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath]]:
        try:
            subprocess.run(c, check=True, capture_output=True, timeout=30, env=env)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return False

# --- TTS (ElevenLabs) ---
ROMANTIC_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah - warm, expressive; or use "Natasha", "Serafina"

def speak_text(text: str) -> None:
    if not elevenlabs_client:
        print("ElevenLabs not configured")
        return
    try:
        audio = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id=ROMANTIC_VOICE_ID,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        temp = "/tmp/teddytalk.mp3"
        if os.name == "nt":
            temp = os.path.join(os.environ.get("TEMP", "."), "teddytalk.mp3")
        with open(temp, "wb") as f:
            if hasattr(audio, "__iter__") and not isinstance(audio, (bytes, str)):
                for chunk in audio:
                    f.write(chunk)
            else:
                f.write(audio)
        _play_audio(temp)
    except Exception as e:
        print(f"TTS Error: {e}")

# --- Gemini poem ---
def get_poem_for_emotion(emotion: str) -> str:
    if not gemini_client:
        return f"I sense you feel {emotion}. Your emotions are valid."
    try:
        prompt = f"""Write a short romantic poem (2-6 lines) for someone who appears {emotion}.
Be empathetic and uplifting. Output only the poem, no quotes or attribution. Keep it brief."""
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = getattr(response, "text", None) or str(response)
        return text.strip().strip('"') if text else f"I sense you feel {emotion}."
    except Exception as e:
        print(f"Gemini error: {e}")
        return f"I sense you feel {emotion}. Your feelings matter."

# --- Emotion mapping (FER+ labels -> internal) ---
_EMOTION_MAP = {
    "anger": "angry", "contempt": "contempt", "disgust": "disgust",
    "fear": "fear", "happiness": "happy", "neutral": "neutral",
    "sadness": "sad", "surprise": "surprise",
}

def _detect_emotion_from_frame(frame):
    if not EMOTION_AVAILABLE:
        return None, {}
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(48, 48))
    if not len(faces):
        return None, {}
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
    # Add padding (~15%) so face isn't cropped too tight - improves FER+ accuracy
    pad = int(0.15 * max(w, h))
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(frame.shape[1], x + w + pad)
    y2 = min(frame.shape[0], y + h + pad)
    face_img = frame[y1:y2, x1:x2]
    face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    emotion, scores = emotion_recognizer.predict_emotions(face_rgb, logits=False)
    emotion_lower = _EMOTION_MAP.get(emotion, emotion.lower())
    emotions = {}
    if hasattr(scores, "__iter__") and not isinstance(scores, (str, bytes)):
        labels = ["neutral", "happiness", "surprise", "sadness", "anger", "disgust", "fear", "contempt"]
        for i, s in enumerate(scores):
            if i < len(labels):
                emotions[_EMOTION_MAP.get(labels[i], labels[i])] = float(s) * 100
    return emotion_lower, emotions

# --- Camera & MJPEG stream ---
_camera = None
_camera_lock = threading.Lock()

def get_camera():
    if not cv2:
        return None
    global _camera
    with _camera_lock:
        if _camera is not None and _camera.isOpened():
            return _camera
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                _camera = cap
                return cap
            cap.release()
        cap = cv2.VideoCapture("/dev/video0")
        if cap.isOpened():
            _camera = cap
            return cap
        return None

def generate_frames():
    cap = get_camera()
    if not cap:
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buf = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")

# --- Message handlers ---
def on_capture(client_id, data=None):
    """Handle capture: grab from USB camera (or use provided image), analyze emotion, poem, speak."""
    global SELECTED_SINK
    data = data or {}
    if not cv2:
        ui.send_message("capture_result", {"error": "OpenCV not available (install libgl1)"})
        return
    try:
        # Select audio sink if provided
        sink = data.get("audio_sink")
        if sink:
            SELECTED_SINK = sink

        image_b64 = data.get("image")
        if image_b64:
            img_bytes = base64.b64decode(image_b64)
            img_arr = cv2.imdecode(
                np.frombuffer(img_bytes, np.uint8),
                cv2.IMREAD_COLOR
            )
        else:
            # Grab from USB camera
            cap = get_camera()
            if not cap:
                ui.send_message("capture_result", {"error": "No camera found"})
                return
            ret, img_arr = cap.read()
            if not ret or img_arr is None:
                ui.send_message("capture_result", {"error": "Could not read from camera"})
                return

        if img_arr is None:
            ui.send_message("capture_result", {"error": "Invalid image"})
            return

        if not EMOTION_AVAILABLE:
            ui.send_message("capture_result", {"error": "Emotion detection not available"})
            return

        emotion, emotions = _detect_emotion_from_frame(img_arr)
        if emotion is None:
            ui.send_message("capture_result", {"error": "No face detected"})
            return

        # Update LCD eyes
        Bridge.call("setEmotion", emotion.upper(), float(emotions.get(emotion, 80)))

        ui.send_message("emotion_update", {
            "emotion": emotion,
            "emotions": emotions,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        poem = get_poem_for_emotion(emotion)
        ui.send_message("poem", {"emotion": emotion, "poem": poem})
        ui.send_message("capture_result", {"ok": True, "emotion": emotion})

        threading.Thread(target=speak_text, args=(poem,), daemon=True).start()

    except Exception as e:
        ui.send_message("capture_result", {"error": str(e)})

def on_bt_scan(client_id, data=None):
    devices = bluetooth_scan()
    ui.send_message("bt_devices", {"devices": devices})

def on_bt_devices(client_id, data=None):
    devices = bluetooth_devices()
    ui.send_message("bt_devices", {"devices": devices})

def on_bt_pair(client_id, data=None):
    data = data or {}
    mac = data.get("mac")
    if not mac:
        ui.send_message("bt_pair_result", {"ok": False, "error": "No MAC"})
        return
    result = bluetooth_pair(mac)
    ui.send_message("bt_pair_result", result)

def on_bt_connect(client_id, data=None):
    data = data or {}
    mac = data.get("mac")
    if not mac:
        ui.send_message("bt_connect_result", {"ok": False, "error": "No MAC"})
        return
    result = bluetooth_connect(mac)
    ui.send_message("bt_connect_result", result)

def on_audio_sinks(client_id, data=None):
    sinks = list_audio_sinks()
    err = "pactl not available" if not shutil.which("pactl") else None
    ui.send_message("audio_sinks", {"sinks": sinks, "error": err})

def on_set_audio_sink(client_id, data=None):
    global SELECTED_SINK
    data = data or {}
    sink = data.get("sink")
    SELECTED_SINK = sink
    ui.send_message("audio_sink_set", {"ok": True, "sink": sink})

# --- MJPEG server (stdlib only, no Flask) ---
def run_mjpeg_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    class MJPEGHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/stream":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for chunk in generate_frames():
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format, *args):
            pass

    try:
        server = ThreadedHTTPServer(("0.0.0.0", 7001), MJPEGHandler)
        server.serve_forever()
    except Exception as e:
        print(f"MJPEG server error: {e}")

# --- Register handlers ---
ui.on_message("capture", on_capture)
ui.on_message("bt_scan", on_bt_scan)
ui.on_message("bt_devices", on_bt_devices)
ui.on_message("bt_pair", on_bt_pair)
ui.on_message("bt_connect", on_bt_connect)
ui.on_message("audio_sinks", on_audio_sinks)
ui.on_message("set_audio_sink", on_set_audio_sink)

# --- Start MJPEG server ---
threading.Thread(target=run_mjpeg_server, daemon=True).start()

# --- Main ---
def _status(ok):
    return "[OK]" if ok else "[--]"
print("Teddy Talk starting...")
print(f"  {_status(EMOTION_AVAILABLE)} Emotion detection")
print(f"  {_status(bool(gemini_client))} Gemini")
print(f"  {_status(bool(elevenlabs_client))} ElevenLabs")
print(f"  {_status(bool(cv2))} OpenCV / camera")
print(f"  {_status(shutil.which('bluetoothctl') is not None)} bluetoothctl")
print(f"  {_status(shutil.which('pactl') is not None)} pactl (audio)")
App.run()
