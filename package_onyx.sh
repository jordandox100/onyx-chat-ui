#!/bin/bash

# ONYX Packaging Script
# Creates distributable package of ONYX

set -e

echo "=================================="
echo "   ONYX Application Packager"
echo "=================================="
echo ""

VERSION="1.0.0"
PACKAGE_NAME="onyx-${VERSION}-linux"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "Creating package: ${PACKAGE_NAME}"
echo ""

# Clean old package
if [ -d "$PACKAGE_DIR" ]; then
    rm -rf "$PACKAGE_DIR"
fi

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Copy application files
echo "Copying application files..."
cp -r desktop_app "$PACKAGE_DIR/"
cp -r Onyx "$PACKAGE_DIR/" 2>/dev/null || mkdir -p "$PACKAGE_DIR/Onyx"
cp requirements.txt "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"
cp INSTALL.md "$PACKAGE_DIR/"
cp DEPLOYMENT.md "$PACKAGE_DIR/"
cp run_onyx.sh "$PACKAGE_DIR/"
cp .env "$PACKAGE_DIR/" 2>/dev/null || echo "CLAUDE_API_KEY=" > "$PACKAGE_DIR/.env"
cp test_onyx.py "$PACKAGE_DIR/"

# Create README in package
cat > "$PACKAGE_DIR/START_HERE.txt" << 'EOF'
ONYX - Local Linux Desktop AI Assistant
========================================

Quick Start:

1. Install dependencies:
   sudo apt-get install qtbase5-dev portaudio19-dev
   pip install -r requirements.txt

2. Configure API key:
   Edit .env file and add your CLAUDE_API_KEY

3. Run ONYX:
   python3 desktop_app/main.py
   
   OR
   
   chmod +x run_onyx.sh
   ./run_onyx.sh

For detailed instructions, see:
- INSTALL.md (Installation guide)
- README.md (Full documentation)
- DEPLOYMENT.md (Deployment options)

Test your installation:
   python3 test_onyx.py

EOF

echo "Creating tarball..."
cd /tmp
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

echo ""
echo "=================================="
echo "Package created successfully!"
echo "=================================="
echo ""
echo "Location: /tmp/${PACKAGE_NAME}.tar.gz"
echo "Size: $(du -h /tmp/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "To extract and use:"
echo "  tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  cd ${PACKAGE_NAME}"
echo "  cat START_HERE.txt"
echo ""
