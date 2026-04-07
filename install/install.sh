#!/bin/bash

# Quick Installation Script
# Run this for express installation

echo "ONYX Quick Installer"
echo "===================\n"

cd "$(dirname "$0")"

if [ -f "setup.sh" ]; then
    chmod +x setup.sh
    ./setup.sh
else
    echo "Error: setup.sh not found!"
    echo "Make sure you're in the /app/install directory."
    exit 1
fi
