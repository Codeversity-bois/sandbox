# Quick start script - Run this after initial setup
# Assumes setup.ps1 has already been run

Write-Host "Starting Sandbox Environment..." -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker ps > $null 2>&1
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running! Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check for .env file
if (-Not (Test-Path ".env")) {
    Write-Host "✗ .env file not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""

# Start the application
python main.py
