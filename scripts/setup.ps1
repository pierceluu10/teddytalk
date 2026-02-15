# Teddy Talk - Pre-download setup for Windows
# Run this before deploying to Arduino UNO Q

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = Split-Path -Parent $ScriptDir

Write-Host "Teddy Talk - Pre-download setup" -ForegroundColor Cyan
Write-Host "App root: $AppRoot"
Write-Host ""

# 1. Download HSEmotion model
Write-Host "[1/2] Downloading HSEmotion ONNX model..." -ForegroundColor Yellow
python "$ScriptDir\download_models.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Model download failed." -ForegroundColor Red
    exit 1
}

# 2. Bundle all Python deps for offline install
if (Test-Path (Join-Path $AppRoot "python\requirements.txt")) {
    Write-Host "[2/2] Bundling Python wheels for offline install..." -ForegroundColor Yellow
    python "$ScriptDir\bundle_all.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Bundle saved to python\bundle\" -ForegroundColor Green
    } else {
        Write-Host "Bundle failed - run: python scripts\bundle_all.py" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Setup complete. Copy the teddytalk folder to your UNO Q." -ForegroundColor Green
