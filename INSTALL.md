# ONYX Installation Guide

## Quick Start

### 1. Prerequisites

Ensure you have a Linux system with:
- Python 3.11 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Audio input device (microphone)

### 2. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    qtbase5-dev \
    qt5-qmake \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    portaudio19-dev \
    python3-pyaudio \
    python3-pip \
    python3-venv
```

### 3. Create Virtual Environment (Recommended)

```bash
cd /app
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: First installation will download:
- PySide6 (~200MB)
- PyTorch (~2GB)
- Whisper model (~150MB on first use)

This may take 10-30 minutes depending on your internet speed.

### 5. Configure API Key

Create or edit `.env` file:

```bash
nano .env
```

Add your Claude API key:

```
CLAUDE_API_KEY=sk-ant-your-actual-api-key-here
```

Get your API key from: https://console.anthropic.com/

### 6. Run ONYX

```bash
# Method 1: Direct
python3 desktop_app/main.py

# Method 2: Using launcher
chmod +x run_onyx.sh
./run_onyx.sh
```

## Verification

After installation, verify everything works:

```bash
# Test imports
python3 -c "
import PySide6
import whisper
import torch
from anthropic.llm.chat import LlmChat
print('✓ All dependencies loaded successfully')
"

# Test ONYX initialization
python3 -c "
from desktop_app.services.storage_service import StorageService
storage = StorageService()
storage.initialize()
print('✓ ONYX initialized successfully')
"
```

## Distribution-Specific Instructions

### Ubuntu 22.04 / 24.04

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    qtbase5-dev \
    portaudio19-dev
    
pip install -r requirements.txt
```

### Debian 12 (Bookworm)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-full \
    python3-pip \
    qtbase5-dev \
    qt5-qmake \
    portaudio19-dev
    
pip install -r requirements.txt
```

### Arch Linux

```bash
sudo pacman -S \
    python \
    python-pip \
    qt6-base \
    portaudio
    
pip install -r requirements.txt
```

### Fedora

```bash
sudo dnf install \
    python3 \
    python3-pip \
    qt5-qtbase-devel \
    portaudio-devel
    
pip install -r requirements.txt
```

## Creating Desktop Entry

To add ONYX to your application menu:

1. Create desktop entry:

```bash
nano ~/.local/share/applications/onyx.desktop
```

2. Add content:

```ini
[Desktop Entry]
Name=ONYX
Comment=Local AI Assistant
Exec=/app/run_onyx.sh
Icon=/app/desktop_app/icon.png
Terminal=false
Type=Application
Categories=Utility;Office;
```

3. Update desktop database:

```bash
update-desktop-database ~/.local/share/applications/
```

## Creating Launcher Icon

Optional: Add an application icon

```bash
# Download or create icon
# Place at: /app/desktop_app/icon.png
# Size: 256x256 or 512x512 PNG
```

## Building Standalone Executable

For distribution without Python dependencies:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller \
    --onefile \
    --windowed \
    --name ONYX \
    --add-data "Onyx:Onyx" \
    --hidden-import PySide6 \
    --hidden-import whisper \
    --hidden-import torch \
    desktop_app/main.py

# Output: dist/ONYX
```

## Common Installation Issues

### Issue: "No module named 'PySide6'"

**Solution**:
```bash
pip uninstall PySide6
pip install PySide6
```

### Issue: "Qt platform plugin could not be initialized"

**Solution**:
```bash
sudo apt-get install libqt5gui5 libqt5widgets5
export QT_QPA_PLATFORM=xcb
```

### Issue: PyAudio installation fails

**Solution**:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install --no-cache-dir PyAudio
```

### Issue: Torch installation is slow

**Solution**: Use CPU-only version:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: "CUDA not available" warning

**Solution**: This is normal. Whisper will use CPU. To use GPU:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Uninstallation

To completely remove ONYX:

```bash
# Remove application files
rm -rf /app/desktop_app

# Remove data (WARNING: deletes all chats)
rm -rf /app/Onyx

# Remove desktop entry
rm ~/.local/share/applications/onyx.desktop

# Uninstall Python packages
pip uninstall -y PySide6 openai-whisper torch torchaudio PyAudio anthropic
```

## Next Steps

After installation:

1. **Configure Personality**: Edit `Onyx/config/personality.txt`
2. **Test Voice Input**: Click the microphone button
3. **Create First Chat**: Click "+ New Chat"
4. **Read Full Documentation**: See `README.md`

## Support

If you encounter issues:

1. Check `Onyx/logs/onyx_*.log`
2. Run with debug output: `python3 desktop_app/main.py 2>&1 | tee debug.log`
3. Verify all dependencies are installed
4. Check the Troubleshooting section in README.md

## System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Linux (any dist) | Ubuntu 22.04+ |
| Python | 3.11 | 3.12 |
| RAM | 4GB | 8GB |
| Disk | 2GB | 5GB |
| CPU | 2 cores | 4+ cores |
| GPU | None | CUDA compatible |
| Display | X11/Wayland | X11/Wayland |
| Audio | Microphone | USB microphone |

---

**Installation complete!** Run `python3 desktop_app/main.py` to start ONYX.
