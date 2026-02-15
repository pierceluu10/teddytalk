# Emotion Poet - Pre-download setup for Windows
# Run this before deploying to Arduino UNO Q

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = Split-Path -Parent $ScriptDir

Write-Host "Emotion Poet - Pre-download setup" -ForegroundColor Cyan
Write-Host "App root: $AppRoot"
Write-Host ""

# 1. Download HSEmotion model
Write-Host "[1/2] Downloading HSEmotion ONNX model..." -ForegroundColor Yellow
python "$ScriptDir\download_models.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Model download failed." -ForegroundColor Red
    exit 1
}

# 2. Create pip download cache for offline install (optional)
$RequirementsPath = Join-Path $AppRoot "python\requirements.txt"
$WheelsDir = Join-Path $AppRoot "python\wheels"
if (Test-Path $RequirementsPath) {
    Write-Host "[2/2] Downloading Python wheels for offline install..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $WheelsDir | Out-Null
    pip download -r $RequirementsPath -d $WheelsDir --platform manylinux2014_aarch64 --python-version 3.11 --only-binary=:all: 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Wheels saved to $WheelsDir" -ForegroundColor Green
    } else {
        Write-Host "Wheel download skipped (optional - may need different platform)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Setup complete. Copy the emotion_poet folder to your UNO Q." -ForegroundColor Green
