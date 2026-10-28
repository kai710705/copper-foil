[CmdletBinding()]
param(
    [int]$Port = 5000,
    [switch]$Development
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw 'Python not found. Install Python 3.12+ or create .venv.'
    }
    $Python = $PythonCommand.Source
}

Write-Host "Python: $Python" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.env')) -and (Test-Path -LiteralPath (Join-Path $ProjectRoot '.env.example'))) {
    Write-Warning 'Missing .env. Copy .env.example and configure SECRET_KEY.'
}

$env:FLASK_APP = 'app.py'
$env:FLASK_DEBUG = if ($Development) { '1' } else { '0' }

& $Python -c "import flask"
if ($LASTEXITCODE -ne 0) {
    throw 'Flask is not installed in the active Python environment. Run .venv\Scripts\python.exe -m pip install -r requirements.txt.'
}

Write-Host "Server: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop.' -ForegroundColor DarkGray

$FlaskArguments = @('-m', 'flask', '--app', 'app.py', 'run', '--host', '127.0.0.1', '--port', "$Port")
if ($Development) { $FlaskArguments += '--debug' }
& $Python @FlaskArguments
exit $LASTEXITCODE
