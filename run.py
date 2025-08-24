#!/usr/bin/env python3
"""
Startup script for the Meeting Summarizer API
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Start the FastAPI application"""
    print("🚀 Starting Intelligent Meeting Summarizer & Action Tracker")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import fastapi
        import transformers
        import torch
        print("✅ Dependencies check passed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"🌐 Server will start on: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 60)
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if debug else "warning"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
