$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = ".\.venv\Scripts\python.exe"

& $python -m compileall -q .
if (-not $?) { exit 1 }
& $python -m ruff check .
if (-not $?) { exit 1 }
& $python -m ruff format --check .
if (-not $?) { exit 1 }
& $python manage.py check
if (-not $?) { exit 1 }
& $python manage.py makemigrations --check --dry-run --noinput
if (-not $?) { exit 1 }
& $python manage.py collectstatic --noinput
if (-not $?) { exit 1 }
& $python manage.py test
if (-not $?) { exit 1 }
& $python manage.py identityforge_health
if (-not $?) { exit 1 }
Write-Host "IdentityForge verification passed."
