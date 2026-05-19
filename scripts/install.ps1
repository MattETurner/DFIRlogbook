$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$VenvPath = Join-Path $RepoRoot ".venv"

python -m venv $VenvPath

$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
& $ActivateScript

python -m pip install --upgrade pip
pip install -r (Join-Path $RepoRoot "requirements.txt")

Write-Host ""
Write-Host "Setup complete."
Write-Host "Activate environment: .\.venv\Scripts\Activate.ps1"
Write-Host "Run app: python .\DFIRlogbook.py"
