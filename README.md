# Teddy Talk — Arduino UNO Q

Face → Emotion → Poem → Personalized Voice

## Features

- **Optional capture**: Live camera preview + capture button to analyze emotion
- **Emotion detection**: FER+ ONNX (lightweight, deepface needed tensorflow for use, taking up too much storage)
- **Poem generation**: Gemini API (2–6 lines, romantic)
- **TTS**: ElevenLabs with personalized voice
- **Robot eyes**: 2× 16×4 I2C LCDs with detailed emotion faces
- **Bluetooth**: Speaker on pi
- **Camera**: USB camera

## Hardware

- Arduino UNO Q
- USB camera
- 2× 16×4 I2C LCD displays (e.g. 0x27 and 0x3F)
- Bluetooth speaker (optional)

## Setup (run before deploying to UNO Q)

### 1. Pre-download models and dependencies

**Windows (PowerShell):**

```powershell
cd teddytalk\scripts
.\setup.ps1
```

**Linux/macOS:**

```bash
cd teddytalk/scripts
./setup.sh
```

This downloads:

- FER+ ONNX model (~19MB) to `python/models/`
- Python wheels for offline install (optional)

### 2. API keys

Copy `.env.example` to `.env` and add your keys:

```
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Deploy to UNO Q

1. **Import**: In App Lab, use **Create new app +** → **Import from folder** (or **Import from .zip**)
2. Select the `teddytalk` folder (or a ZIP of it)
3. App Lab installs dependencies automatically. Uses `opencv-python-headless` only (no libGL). If packages are missing, SSH in and run `scripts/setup_on_device.sh`.
4. Run the app in App Lab
5. Open the web UI (URL shown in App Lab, e.g. http://10.197.243.162:7000)

**If you get "405 Method Not Allowed" or "app is broken or misconfigured":**

- Try **Import from folder** instead of ZIP (or vice versa)
- Ensure the folder path has no special characters
- Ensure you have internet (App Lab fetches brick metadata)
- Try creating a new app and copying files in via App Lab's file browser

## I2C LCD addresses

Default: left eye `0x27`, right eye `0x3F`. Adjust in `sketch/sketch.ino` if your LCDs use different addresses. Use an I2C scanner to find addresses.

## Troubleshooting

| Issue                                     | Solution                                                                                           |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------- |
| "No module named ..."                     | Python packages not installed. Re-import the app or run `scripts/setup_on_device.sh` on the UNO Q. |
| "bluetoothctl: No such file or directory" | App runs in a container without Bluetooth tools. Use **SBC mode** for full Bluetooth.              |
| "pactl: No such file or directory"        | Same as above – use SBC mode for audio sink selection.                                             |
| Camera not available                      | Check USB camera is connected.                                                                     |
