#!/bin/bash

# Voyager Application Startup Script
# This script starts both the FastAPI backend and Streamlit frontend

echo "🚀 Starting voyager Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📥 Installing dependencies (this may take a few minutes)..."
    pip install -q -r requirements.txt
    touch venv/.dependencies_installed
    echo "✅ Dependencies installed"
fi

# Kill any existing processes on ports 8000 and 8501
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Start FastAPI backend
echo ""
echo "🔷 Starting FastAPI Backend Server (port 8000)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 5

# Start Streamlit frontend
echo ""
echo "🔶 Starting Streamlit Frontend (port 8501)..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "   Streamlit PID: $STREAMLIT_PID"

# Wait for Streamlit to start
sleep 5

echo ""
echo "✅ Voyager Application Started Successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 ACCESS YOUR APPLICATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   🏠 Dashboard:     http://localhost:8000/static/dashboard.html"
echo "   🔍 Athena Runner: http://localhost:8000/static/athena.html"
echo "   📊 Data Analysis: http://localhost:8501"
echo "   ⚙️  Admin Panel:   http://localhost:8000/static/admin.html"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 DEFAULT LOGIN:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Logs are available in:"
echo "   Backend:  logs/backend.log"
echo "   Streamlit: logs/streamlit.log"
echo ""
echo "🛑 To stop the application, run: ./stop.sh"
echo ""
