$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "=== AETHER Python SDK test runner ===" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host ""
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
python --version

Write-Host ""
Write-Host "[2/5] Installing SDK in editable mode..." -ForegroundColor Yellow
python -m pip install -e .

Write-Host ""
Write-Host "[3/5] Running py_compile on SDK files..." -ForegroundColor Yellow
python -m py_compile .\aether_sdk\client.py
python -m py_compile .\aether_sdk\models.py
python -m py_compile .\aether_sdk\__init__.py

Write-Host ""
Write-Host "[4/5] Running py_compile on test files..." -ForegroundColor Yellow
Get-ChildItem .\tests\test_*.py | ForEach-Object {
    python -m py_compile $_.FullName
}

Write-Host ""
Write-Host "[5/5] Running unittest discover..." -ForegroundColor Yellow
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host ""
Write-Host "=== All SDK tests completed successfully ===" -ForegroundColor Green