$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Create it first with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location '$PSScriptRoot'; & '$python' -m uvicorn tracking_api:app --reload --port 8000")
Start-Sleep -Seconds 2
& $python -m streamlit run homepage.py
