#!/usr/bin/env python
"""
Startup script for the Intelligent RAG Data Analysis Tool
"""
import sys
import subprocess
from pathlib import Path


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
        import langchain
        import chromadb
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True


def main():
    """Main startup function"""
    print("🚀 Starting Intelligent RAG Data Analysis Tool...")
    print()

    # Check environment
    if not check_env_file():
        print("\n⚠️  Please configure .env file and run again")
        return

    # Check dependencies
    check_dependencies()

    print("\n🌐 Starting server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("\n⏹️  Press CTRL+C to stop the server\n")

    # Start uvicorn
    subprocess.call([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


if __name__ == "__main__":
    main()
