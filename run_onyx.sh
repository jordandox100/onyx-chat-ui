#!/bin/bash

# ONYX Launcher Script
# This script launches the ONYX desktop application

set -e

echo "=================================="
echo "   ONYX - AI Assistant Launcher"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo "Warning: Python $PYTHON_VERSION detected. Python 3.11+ recommended."
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "Creating .env file. Please add your CLAUDE_API_KEY."
    echo "CLAUDE_API_KEY=" > .env
fi

# Check if API key is set
if ! grep -q "CLAUDE_API_KEY=." .env; then
    echo ""
    echo "Warning: CLAUDE_API_KEY not set in .env file."
    echo "Please edit .env and add your API key:"
    echo "  CLAUDE_API_KEY=your_key_here"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Onyx directory exists
if [ ! -d "Onyx" ]; then
    echo "Creating Onyx data directory..."
    mkdir -p Onyx/{history,config,voice,logs}
fi

echo "Starting ONYX..."
echo ""

# Launch ONYX
cd /app
python3 desktop_app/main.py

echo ""
echo "ONYX has been closed."
