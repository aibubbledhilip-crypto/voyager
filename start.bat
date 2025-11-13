@echo off
REM Voyager Application Startup Script for Windows
REM Batch script to start both FastAPI backend and Streamlit frontend

echo.
echo ======================================================================
echo   Starting voyager Application...
echo ======================================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\.dependencies_installed" (
    echo Installing dependencies - this may take a few minutes...
    pip install -q -r requirements.txt
    type nul > venv\.dependencies_installed
    echo Dependencies installed successfully!
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Kill existing processes (if any)
echo Cleaning up existing processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" 2>nul

REM Start FastAPI backend in new window
echo.
echo Starting FastAPI Backend Server on port 8000...
start "Voyager Backend (FastAPI)" cmd /k "venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start Streamlit frontend in new window
echo Starting Streamlit Frontend on port 8501...
start "Voyager Frontend (Streamlit)" cmd /k "venv\Scripts\activate.bat && streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"

REM Wait for Streamlit to start
timeout /t 5 /nobreak >nul

echo.
echo ======================================================================
echo   Voyager Application Started Successfully!
echo ======================================================================
echo.
echo   ACCESS YOUR APPLICATION:
echo   ------------------------
echo.
echo   Dashboard:     http://localhost:8000/static/dashboard.html
echo   Athena Runner: http://localhost:8000/static/athena.html
echo   Data Analysis: http://localhost:8501
echo   Admin Panel:   http://localhost:8000/static/admin.html
echo.
echo   DEFAULT LOGIN:
echo   --------------
echo   Username: admin
echo   Password: admin123
echo.
echo ======================================================================
echo   Two new command windows have opened.
echo   Close those windows to stop the servers.
echo ======================================================================
echo.
pause
