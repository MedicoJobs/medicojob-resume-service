$ErrorActionPreference = "Stop"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $python) {
  Write-Error "Python was not found. Use Docker instead: docker compose up --build"
}

if ($python.Name -eq "py.exe") {
  $versionOutput = py -3.12 --version 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.12 is required for local install. Current Python 3.14 cannot build required native packages. Install Python 3.12 or use Docker: docker compose up --build"
  }
  py -3.12 -m pip install -r requirements.txt
  py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 5008
} else {
  $version = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
  if ($version -notin @("3.11", "3.12")) {
    Write-Error "Python $version is not supported for this service. Use Python 3.11/3.12 or Docker: docker compose up --build"
  }
  python -m pip install -r requirements.txt
  python -m uvicorn app.main:app --host 0.0.0.0 --port 5008
}
