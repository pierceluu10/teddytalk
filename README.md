# Teddy Talk — Arduino UNO Q

Face → Emotion → Poem → Personalized Voice

## Features

- **Capture**: Web button or physical button on Arduino pin 2 to analyze emotion
- **Emotion detection**: FER+ ONNX (lightweight, deepface needed tensorflow for use, taking up too much storage)
- **Poem generation**: Gemini API (2–6 lines, romantic)
- **TTS**: ElevenLabs with personalized voice
- **Robot eyes**: 2× SSD1306 OLED (128×32) or 2× 16×4 I2C LCDs with emotion expressions
- **Bluetooth**: Speaker on pi
- **Camera**: USB camera

## Hardware

- Arduino UNO Q
- USB camera
- 2× SSD1306 OLED (128×32) on same I2C address (0x3C), or 2× 16×4 I2C LCD displays
- Button on digital pin 2 (optional) – triggers capture like the web button
- Bluetooth speaker (optional)

## Setup (run before deploying to UNO Q)

### 1. Pre-download models and dependencies (one-time bundle)

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

Or run the full bundle script directly:

```bash
python scripts/bundle_all.py
```

This downloads:

- FER+ ONNX model (~34 MB) to `python/models/`
- All Python wheels to `python/bundle/wheels/` for offline install on UNO Q

### 2. API keys

Use either `.env` or separate key files:

**Option A – `.env`:** Copy `.env.example` to `.env` and add:
```
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

**Option B – Separate files:** Create `python/gemini_api_key.txt` and `python/elevenlabs_api_key.txt`, each with just the API key on a single line (no extra text).

**On UNO Q (SBC mode):** The key files are in `.gitignore`. If you import the project, add the key files manually via App Lab's file browser or SSH: place `gemini_api_key.txt` and `elevenlabs_api_key.txt` in the `python/` folder on the device.

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

## I2C display addresses

- **SSD1306 OLED**: Default address `0x3C`. Two displays on the same address mirror each other.
- **16×4 LCD**: Left eye `0x27`, right eye `0x3F`. Adjust in `sketch/sketch.ino` if needed.

## Troubleshooting

| Issue                                     | Solution                                                                                           |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------- |
| "No module named ..."                     | Python packages not installed. Re-import the app or run `scripts/setup_on_device.sh` on the UNO Q. |
| "bluetoothctl: No such file or directory" | Bluetooth only available in SBC mode. UI shows "Bluetooth only available in SBC mode".           |
| "pactl: No such file or directory"        | PulseAudio not available. App falls back to paplay → mpv → ffplay → ffmpeg+aplay → pygame.         |
| Camera not available                      | Check USB camera is connected.                                                                     |
| No poem / "Your emotions are valid"      | Gemini API key missing or invalid. Check startup log for "[!] No Gemini API key". Add key files.   |
| No sound / TTS not playing                | Install mpv: `sudo apt install mpv`. YouTube plays in browser; this app needs mpv/paplay for TTS.  |
| "ElevenLabs quota/credits exceeded"      | Add credits at elevenlabs.io. Free tier has monthly limits.                                      |
