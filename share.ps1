# BloodLink - temporary public link (Cloudflare Quick Tunnel)
#
# How to use:
#   1. Start the app in one terminal:
#        .\.venv\Scripts\python.exe run.py
#   2. Run this script in a second terminal:
#        .\share.ps1
#   3. Copy the https://....trycloudflare.com link it prints and share it.
#
# The link works only while BOTH terminals stay open.

$ErrorActionPreference = "Stop"

$cloudflared = Join-Path $env:LOCALAPPDATA "cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflared)) {
    $found = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($found) {
        $cloudflared = $found.Source
    } else {
        Write-Host "cloudflared was not found." -ForegroundColor Red
        Write-Host "Install it with:" -ForegroundColor Yellow
        Write-Host "  winget install --id Cloudflare.cloudflared" -ForegroundColor Cyan
        exit 1
    }
}

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 5
    Write-Host "BloodLink is running locally (HTTP $($response.StatusCode))." -ForegroundColor Green
} catch {
    Write-Host "BloodLink is NOT running on port 5000." -ForegroundColor Red
    Write-Host "Open another terminal and run:" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\python.exe run.py" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Starting the public tunnel (press Ctrl+C to stop)..." -ForegroundColor Cyan
Write-Host "Look for the https://....trycloudflare.com link below." -ForegroundColor Cyan
Write-Host ""

& $cloudflared tunnel --url http://127.0.0.1:5000 --no-autoupdate
