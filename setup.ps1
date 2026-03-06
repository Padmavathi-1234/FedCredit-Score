# FedCredit Score - Environment Setup Script (PowerShell)
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "FedCredit Score - Environment Setup" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check/Create Virtual Environment
Write-Host "[1] Checking for virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[INFO] Virtual environment not found. Creating a new one in 'venv'..." -ForegroundColor Gray
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment. Ensure Python is installed." -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "[INFO] Virtual environment 'venv' already exists." -ForegroundColor Green
}

Write-Host ""

# 2. Activate Virtual Environment
Write-Host "[2] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""

# 3. Install Dependencies
Write-Host "[3] Installing/Updating project and dependencies..." -ForegroundColor Yellow
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Gray
python -m pip install --upgrade pip
Write-Host "[INFO] Installing the project in editable mode..." -ForegroundColor Gray
pip install -e .

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "To run the application, use the following commands:"
Write-Host ""
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "    uvicorn backend.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host ""
