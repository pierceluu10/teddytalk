# Emotion Poet — Storage Audit (1.5 GB Limit)

## Current App Size (files only)

| Component | Size |
|-----------|------|
| App folder (code, assets, model) | ~15 MB |
| HSEmotion model (python/models/*.onnx) | ~16 MB |

## Python Dependencies (pip install on device)

| Package | Est. Size | Notes |
|---------|-----------|-------|
| opencv-python-headless | ~50–80 MB | Headless = no GUI; smaller than full opencv |
| onnxruntime | ~50–60 MB | CPU-only |
| hsemotion-onnx | ~1 MB | + numpy, onnx (pulled as deps) |
| numpy | ~20 MB | Required by opencv, hsemotion |
| google-genai | ~15 MB | Gemini API client |
| elevenlabs | ~5 MB | TTS API client |
| flask | ~5 MB | MJPEG stream server |
| **Subtotal** | **~150–200 MB** | Conservative |

## Brick (shared, not per-app)

| Brick | Role | Storage |
|-------|------|---------|
| arduino:web_ui | Serves HTML, Socket.IO | Shared container; first use may download ~100–200 MB |

## Total Estimate

| Scenario | Size |
|----------|------|
| Our app + pip packages | ~165–215 MB |
| + First-time web_ui brick | +100–200 MB (one-time, shared) |
| **Worst case** | **~400 MB** |
| **Typical** | **~250 MB** |

**Verdict: Well under 1.5 GB** (≈25% of limit at worst).

## Comparison

- obj_detect_tts (similar stack): documented as ~600 MB
- Emotion Poet: lighter (ElevenLabs vs Google TTS, no pygame)

## Optimizations (if needed)

1. **Pre-download wheels** — Run `scripts/setup.ps1` before deploy to avoid on-device pip download.
2. **Use cloud_llm brick** — Could replace google-genai, but adds a brick; net effect unclear.
3. **Keep opencv-python-headless** — Already the smallest OpenCV variant.
