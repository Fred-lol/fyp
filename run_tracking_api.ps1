Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m uvicorn tracking_api:app --reload --port 8000
