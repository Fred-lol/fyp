<#
  Starts AquaLoad for a private local network.
  - Streamlit listens on the LAN, not just localhost.
  - The tracking API starts with it.
  - Existing instances are reused, so double-clicking the launcher is safe.
#>

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Join-Path $projectDirectory ".venv\Scripts\python.exe"
$streamlitExecutable = Join-Path $projectDirectory ".venv\Scripts\streamlit.exe"

function Test-AquaLoadPort([int]$port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

$networkAddress = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -match '^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)' -and
        $_.PrefixOrigin -ne 'WellKnown'
    } |
    Select-Object -First 1 -ExpandProperty IPAddress

if (-not $networkAddress) {
    throw "AquaLoad could not find a private Wi-Fi or Ethernet address. Connect the laptop to your local network and try again."
}

# Streamlit makes API requests on the laptop, not in the iPad browser. Keep
# this loopback URL stable even when Wi-Fi assigns the laptop a new LAN IP.
# iPads only need the Streamlit URL saved below.
$env:AQUALOAD_TRACKING_API = "http://127.0.0.1:8000"

if (-not (Test-AquaLoadPort 8000)) {
    Start-Process -FilePath $pythonExecutable -WorkingDirectory $projectDirectory -WindowStyle Hidden -ArgumentList @(
        "-m", "uvicorn", "tracking_api:app", "--host", "0.0.0.0", "--port", "8000"
    )
}

if (-not (Test-AquaLoadPort 8501)) {
    Start-Process -FilePath $streamlitExecutable -WorkingDirectory $projectDirectory -WindowStyle Hidden -ArgumentList @(
        "run", "homepage.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"
    )
}

# Save the current LAN address for quick reference. It is recreated every
# time the launcher runs, so it stays correct if the router assigns a new IP.
Set-Content -Path (Join-Path $projectDirectory "AquaLoad-LAN-URL.txt") -Value "http://${networkAddress}:8501" -Encoding utf8
