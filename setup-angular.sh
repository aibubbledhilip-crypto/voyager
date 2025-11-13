#!/bin/bash

# Voyager Angular Frontend Setup Script

echo "=========================================="
echo "   Voyager Angular Frontend Setup"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install nodejs npm"
    echo ""
    echo "On macOS:"
    echo "  brew install node"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Check if Angular CLI is installed
if ! command -v ng &> /dev/null; then
    echo "📦 Installing Angular CLI globally..."
    npm install -g @angular/cli
    echo "✅ Angular CLI installed"
else
    echo "✅ Angular CLI version: $(ng version --minimal)"
fi

echo ""

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "=========================================="
echo "   Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start FastAPI backend (Terminal 1):"
echo "   cd $(pwd)/.."
echo "   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. Start Angular frontend (Terminal 2):"
echo "   cd $(pwd)"
echo "   npm start"
echo ""
echo "The app will open at: http://localhost:4200"
echo ""
echo "=========================================="
echo ""
echo "Next Steps:"
echo "  1. Read ANGULAR_SETUP.md for full documentation"
echo "  2. Read ANGULAR_MIGRATION.md for migration guide"
echo "  3. Implement components following the examples"
echo "  4. Run 'npm test' to run unit tests"
echo ""
echo "Happy coding! 🚀"
echo ""
