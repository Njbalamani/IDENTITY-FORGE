$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

if (-not (Test-Path -LiteralPath ".venv")) {
    py -3.12 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}

& ".\.venv\Scripts\python.exe" manage.py migrate
& ".\.venv\Scripts\python.exe" manage.py collectstatic --noinput
& ".\.venv\Scripts\python.exe" manage.py generate_sample_data
& ".\.venv\Scripts\python.exe" manage.py seed_identityforge
Write-Host "IdentityForge setup complete. Run scripts\dev.ps1 to start the server."
