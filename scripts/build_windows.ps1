$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python -m pip install -r requirements.txt
python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name "DeatonAutoImageStudio" `
    --icon "$root\resources\branding\deaton_auto.ico" `
    --add-data "$root\config;config" `
    --add-data "$root\resources;resources" `
    "$root\app\main.py"

Write-Host "Built: $root\dist\DeatonAutoImageStudio.exe"
