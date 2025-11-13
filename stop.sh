#!/bin/bash

# Voyager Application Stop Script
# This script stops both the FastAPI backend and Streamlit frontend

echo "🛑 Stopping voyager Application..."
echo ""

# Kill processes on ports 8000 and 8501
echo "   Stopping FastAPI Backend (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "   No process found on port 8000"

echo "   Stopping Streamlit Frontend (port 8501)..."
lsof -ti:8501 | xargs kill -9 2>/dev/null || echo "   No process found on port 8501"

echo ""
echo "✅ Voyager Application Stopped"
echo ""
