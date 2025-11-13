# Voyager Angular Frontend Setup Script for Windows PowerShell

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Voyager Angular Frontend Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
    $npmVersion = npm --version
    Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Check if Angular CLI is installed
try {
    $ngVersion = ng version --minimal 2>$null
    Write-Host "✅ Angular CLI installed" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing Angular CLI globally..." -ForegroundColor Yellow
    npm install -g @angular/cli
    Write-Host "✅ Angular CLI installed" -ForegroundColor Green
}

Write-Host ""

# Navigate to frontend directory
Set-Location -Path "frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    npm install
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host ""
Write-Host "1. Start FastAPI backend (Terminal 1):" -ForegroundColor Yellow
Write-Host "   cd $(Resolve-Path ..\)" -ForegroundColor White
Write-Host "   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "2. Start Angular frontend (Terminal 2):" -ForegroundColor Yellow
Write-Host "   cd $(Get-Location)" -ForegroundColor White
Write-Host "   npm start" -ForegroundColor White
Write-Host ""
Write-Host "The app will open at: http://localhost:4200" -ForegroundColor Cyan
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Read ANGULAR_SETUP.md for full documentation"
Write-Host "  2. Read ANGULAR_MIGRATION.md for migration guide"
Write-Host "  3. Implement components following the examples"
Write-Host "  4. Run 'npm test' to run unit tests"
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Green
Write-Host ""
