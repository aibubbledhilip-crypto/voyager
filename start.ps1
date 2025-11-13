# Voyager Application Startup Script for Windows
# PowerShell script to start both FastAPI backend and Streamlit frontend

Write-Host "🚀 Starting voyager Application..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies if needed
if (-not (Test-Path "venv\.dependencies_installed")) {
    Write-Host "📥 Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    pip install -q -r requirements.txt
    New-Item -Path "venv\.dependencies_installed" -ItemType File -Force | Out-Null
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# Kill any existing processes on ports 8000 and 8501
Write-Host "🧹 Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
}

# Start FastAPI backend in a new window
Write-Host ""
Write-Host "🔷 Starting FastAPI Backend Server (port 8000)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

# Wait for backend to start
Start-Sleep -Seconds 5

# Start Streamlit frontend in a new window
Write-Host "🔶 Starting Streamlit Frontend (port 8501)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"

# Wait for Streamlit to start
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "✅ Voyager Application Started Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "📊 ACCESS YOUR APPLICATION:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "   🏠 Dashboard:     http://localhost:8000/static/dashboard.html" -ForegroundColor White
Write-Host "   🔍 Athena Runner: http://localhost:8000/static/athena.html" -ForegroundColor White
Write-Host "   📊 Data Analysis: http://localhost:8501" -ForegroundColor White
Write-Host "   ⚙️  Admin Panel:   http://localhost:8000/static/admin.html" -ForegroundColor White
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "🔑 DEFAULT LOGIN:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "   Username: admin" -ForegroundColor Yellow
Write-Host "   Password: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Two new PowerShell windows have opened for Backend and Streamlit" -ForegroundColor Green
Write-Host "   Close those windows to stop the servers" -ForegroundColor Green
Write-Host ""
