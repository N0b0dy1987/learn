<#
PowerShell setup script for the Mir project.
It will create a virtual environment (.venv), activate it, install requirements,
and copy config.template.json to config.json if config.json does not exist.

Usage: open PowerShell in project root and run:
    .\scripts\setup.ps1
#>

Write-Host "Creating virtual environment .venv if missing..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
& .venv\Scripts\Activate.ps1

Write-Host "Installing requirements..."
pip install -r requirements.txt

if (-not (Test-Path "config.json")) {
    if (Test-Path "config.template.json") {
        Copy-Item config.template.json config.json
        Write-Host "Copied config.template.json -> config.json. Please edit config.json and set adb_path."
    } else {
        Write-Host "No config.template.json found. Please create config.json manually."
    }
} else {
    Write-Host "config.json already exists; skipping copy."
}

Write-Host "Setup complete. To run the app: python app.py"