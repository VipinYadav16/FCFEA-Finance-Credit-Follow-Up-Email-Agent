$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

function Get-PythonForVenv {
    param(
        [string]$preferredVersion
    )

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher -and $preferredVersion) {
        return @($pyLauncher.Path, "-$preferredVersion")
    }

    return @("python")
}

function Ensure-Venv {
    param(
        [string]$venvPath,
        [string]$requirementsPath,
        [string[]]$pythonCommand
    )

    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating venv at $venvPath"
        & $pythonCommand -m venv $venvPath
    }

    $py = Join-Path $venvPath "Scripts/python.exe"
    if (-not (Test-Path $py)) {
        throw "Python not found in venv: $py"
    }

    Write-Host "Installing dependencies from $requirementsPath"
    $null = & $py -m pip install -r $requirementsPath

    return $py
}

$backendVenv = Join-Path $repoRoot ".venv"
$backendReqs = Join-Path $repoRoot "requirements.txt"
$backendPythonCmd = Get-PythonForVenv -preferredVersion "3.12"
$backendPy = Ensure-Venv -venvPath $backendVenv -requirementsPath $backendReqs -pythonCommand $backendPythonCmd

$frontendVenv = Join-Path $repoRoot "frontend/.venv"
$frontendReqs = Join-Path $repoRoot "frontend/requirements.txt"
$frontendPythonCmd = Get-PythonForVenv -preferredVersion "3.12"
$frontendPy = Ensure-Venv -venvPath $frontendVenv -requirementsPath $frontendReqs -pythonCommand $frontendPythonCmd

Write-Host "Starting backend (http://127.0.0.1:8000)"
Start-Process -FilePath $backendPy -WorkingDirectory $repoRoot -ArgumentList @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--app-dir",
    "backend",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
    "--reload"
)

Write-Host "Waiting for backend health..."
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # keep retrying
    }
}
if (-not $backendReady) {
    Write-Warning "Backend did not become ready in time. Frontend may show temporary connectivity errors."
}

Write-Host "Starting frontend (http://localhost:8501)"
if (-not $env:BACKEND_URL) {
    $env:BACKEND_URL = "http://127.0.0.1:8000"
}
Start-Process -FilePath $frontendPy -WorkingDirectory $repoRoot -ArgumentList @(
    "-m",
    "streamlit",
    "run",
    "frontend/streamlit_app.py"
)

Write-Host "Done. Backend and frontend are starting in separate processes."
