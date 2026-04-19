$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python 3.11+ was not found. Install Python and rerun setup."
}

function Invoke-CommandArray {
    param (
        [string[]]$Command,
        [string[]]$Arguments
    )

    if ($Command.Length -gt 1) {
        $baseArguments = $Command[1..($Command.Length - 1)]
        & $Command[0] @baseArguments @Arguments
    } else {
        & $Command[0] @Arguments
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $($Command -join ' ') $($Arguments -join ' ')"
    }
}

Write-Host "=== WeGoComply Setup Script (PowerShell) ==="
Write-Host ""

$pythonCommand = Get-PythonCommand
$venvDir = Join-Path $backendDir "venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

Write-Host "=== Setting up Backend ==="
if (-not (Test-Path (Join-Path $backendDir ".env"))) {
    Copy-Item (Join-Path $backendDir ".env.example") (Join-Path $backendDir ".env")
    Write-Host "Created backend/.env. Review WEGOCOMPLY_MODE and API keys before running in live mode."
} else {
    Write-Host "backend/.env already exists"
}

if (-not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment..."
    Invoke-CommandArray -Command $pythonCommand -Arguments @("-m", "venv", $venvDir)
} else {
    Write-Host "Python virtual environment already exists"
}

Write-Host "Installing backend dependencies..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }
& $venvPython -m pip install -r (Join-Path $backendDir "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install backend requirements." }

Write-Host ""
Write-Host "=== Setting up Frontend ==="
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Push-Location $frontendDir
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies." }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "frontend/node_modules already exists"
}

Write-Host ""
Write-Host "=== Setup Complete ==="
Write-Host ""
Write-Host "Backend:"
Write-Host "  cd backend"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  uvicorn main:app --reload"
Write-Host ""
Write-Host "Frontend:"
Write-Host "  cd frontend"
Write-Host "  npm run dev"
