#!/usr/bin/env python
"""
Startup script for the Streamlit GUI

This script starts both the FastAPI backend and Streamlit frontend
"""
import sys
import subprocess
import time
from pathlib import Path
import os


def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("📝 Creating .env from .env.example...")
        example = Path(".env.example")
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
            print("✅ Created .env file")
            print("⚡ Please edit .env and add your API keys before running!")
            return False
        else:
            print("❌ .env.example not found. Please create .env manually.")
            return False
    return True


def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import streamlit
        import plotly
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True


def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Give backend time to start
    return backend_process


def start_streamlit():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit GUI...")
    subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"])


def main():
    """Main startup function"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Intelligent RAG Data Analysis Tool - GUI Launcher      ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Check environment
    if not check_env_file():
        print("\n⚠️  Please configure .env file and run again")
        return

    # Check dependencies
    check_dependencies()

    print("\n🌐 Starting services...")
    print("📍 API will be available at: http://localhost:8000")
    print("📍 Web GUI will be available at: http://localhost:8501")
    print("\n⏹️  Press CTRL+C to stop all services\n")

    # Start backend
    backend_process = start_backend()

    try:
        # Start Streamlit (this will block)
        start_streamlit()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        # Clean up backend process
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()
