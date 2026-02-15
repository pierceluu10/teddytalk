# teddytalk🧸🗣️ — Arduino UNO Q

Face → Emotion → Poem → Personalized Voice

## Features

- **Capture**: Button on Arduino pin 2 to analyze emotion
- **Emotion detection**: FER+ ONNX (lightweight, deepface needed tensorflow for use, taking up too much storage)
- **Poem ("Love Message") generation**: Gemini API (2–6 lines)
- **TTS**: ElevenLabs with personalized voice
- **Bluetooth**: Cool bluetooth speaker
- **Camera**: USB camera

## Hardware

- Arduino UNO Q
- USB camera
- 2× SSD1306 OLED (128×32) on same I2C address (0x3C)
- Button on digital pin – triggers capture
- Bluetooth speaker

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

 `.env`:** Copy `.env.example` to `.env` and add:
```
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Deploy to UNO Q

1. **Import**: In App Lab, use **Create new app +** → **Import from folder** (or **Import from .zip**)
2. Select the `teddytalk` folder (or a ZIP of it)
3. App Lab installs dependencies automatically. Uses `opencv-python-headless` only. If packages are missing, SSH in and run `scripts/setup_on_device.sh`.
4. Run the app in App Lab

## The whole process

1. **Capture** — Open the web UI on your phone or laptop. You see a live camera feed. When you’re ready, capture.

2. **Emotion** — The photo goes to the UNO Q. OpenCV finds a face, and the FER+ model guesses the emotion (happy, sad, surprised, etc.). The Arduino OLEDs update to show that emotion on the robot’s “eyes.” (implementation in the works for the OLEDs)

3. **Teddy Message** — The detected emotion is sent to Gemini, which returns a short romantic poem (2–6 lines) in that mood.

4. **Voice** — ElevenLabs turns the poem into speech using your chosen voice. Audio plays over the Bluetooth speaker or the board’s default output. 
