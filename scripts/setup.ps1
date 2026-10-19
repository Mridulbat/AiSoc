$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
py -3.10 -m venv .venv
if ($LASTEXITCODE) { throw 'Install Python 3.10 (or create .venv with Python 3.11 manually).' }
# Use the installed interpreter for downloads; some Windows firewall rules block venv executables.
py -3.10 -m pip install --target .venv/Lib/site-packages --upgrade -r requirements.txt
if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
Push-Location frontend
try {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE) { throw 'npm ci failed.' }
    npm run build
    if ($LASTEXITCODE) { throw 'Frontend build failed.' }
} finally { Pop-Location }
