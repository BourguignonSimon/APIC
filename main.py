#!/usr/bin/env python3
"""
APIC - Agentic Process Improvement Consultant
Main entry point for running the application.

Usage:
    python main.py api      - Run the FastAPI backend
    python main.py frontend - Run the Streamlit frontend
    python main.py all      - Run both (requires separate terminals)
"""

import os
import sys
import argparse
import subprocess


def run_api():
    """Run the FastAPI backend server."""
    import uvicorn
    from config.settings import settings

    print("Starting APIC API server...")
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


def run_frontend():
    """Run the Streamlit frontend."""
    from config.settings import settings

    print("Starting APIC Streamlit frontend...")
    subprocess.run([
        "streamlit", "run",
        "frontend/app.py",
        "--server.port", str(settings.STREAMLIT_PORT),
        "--server.address", "0.0.0.0",
    ])


def main():
    parser = argparse.ArgumentParser(
        description="APIC - Agentic Process Improvement Consultant"
    )
    parser.add_argument(
        "command",
        choices=["api", "frontend", "all"],
        help="Component to run",
    )

    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "frontend":
        run_frontend()
    elif args.command == "all":
        print("To run both components, open two terminals:")
        print("  Terminal 1: python main.py api")
        print("  Terminal 2: python main.py frontend")
        sys.exit(0)


if __name__ == "__main__":
    main()
