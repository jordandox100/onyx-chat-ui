#!/bin/bash

##############################################
# ONYX Desktop AI Assistant - Installation   #
# Automated setup script for Linux           #
# Uses Python venv for clean dependency mgmt #
##############################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "========================================================="
echo "        ONYX Desktop AI Assistant Installer              "
echo "========================================================="
echo -e "${NC}"

# Resolve absolute path of the project root (one level up from install/)
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$INSTALL_DIR/.venv"

echo -e "${GREEN}Project directory: ${INSTALL_DIR}${NC}"

print_step()  { echo -e "\n${BLUE}=== $1 ===${NC}"; }
print_ok()    { echo -e "${GREEN}  [OK] $1${NC}"; }
print_warn()  { echo -e "${YELLOW}  [WARN] $1${NC}"; }
print_err()   { echo -e "${RED}  [FAIL] $1${NC}"; }

# ── 1. Check Python ──────────────────────────────────────────
print_step "Checking Python"
if ! command -v python3 &>/dev/null; then
    print_err "python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    print_err "Python 3.10+ required (found $PY_VER)."
    exit 1
fi
print_ok "Python $PY_VER"

# ── 2. Install system packages ───────────────────────────────
print_step "Installing system packages"

install_apt() {
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3-venv python3-dev \
        portaudio19-dev \
        espeak-ng \
        libxcb-xinerama0 libxcb-cursor0 \
        build-essential 2>&1 | tail -1
}

install_dnf() {
    sudo dnf install -y \
        python3-devel portaudio-devel espeak-ng gcc gcc-c++ 2>&1 | tail -1
}

install_pacman() {
    sudo pacman -S --noconfirm --needed \
        python portaudio espeak-ng base-devel 2>&1 | tail -1
}

if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
        ubuntu|debian|pop|linuxmint|zorin) install_apt ;;
        fedora|rhel|centos|rocky|alma)     install_dnf ;;
        arch|manjaro|endeavouros)          install_pacman ;;
        *) print_warn "Unknown distro ($ID). You may need to install portaudio and espeak-ng manually." ;;
    esac
else
    print_warn "Cannot detect distro. Install portaudio19-dev and espeak-ng manually if needed."
fi
print_ok "System packages"

# ── 3. Create virtual environment ────────────────────────────
print_step "Setting up Python virtual environment"
if [ -d "$VENV_DIR" ]; then
    print_warn "Existing venv found at $VENV_DIR — reusing it"
else
    python3 -m venv "$VENV_DIR"
    print_ok "Created venv at $VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
print_ok "Activated venv ($(python3 --version))"

# Upgrade pip
pip install --upgrade pip --quiet

# ── 4. Install Python dependencies ───────────────────────────
print_step "Installing Python packages (this may take a few minutes)"
cd "$INSTALL_DIR"

# Install emergentintegrations from private index
pip install emergentintegrations \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ \
    --quiet 2>&1 | tail -2
print_ok "emergentintegrations"

# Install the rest from requirements.txt (skip emergentintegrations line)
grep -v '^emergentintegrations' requirements.txt | pip install -r /dev/stdin \
    --quiet 2>&1 | tail -2
print_ok "All Python packages installed"

# ── 5. Initialise ONYX data folders ─────────────────────────
print_step "Initialising ONYX data structure"
python3 -c "
from desktop_app.services.storage_service import StorageService
s = StorageService()
s.initialize()
print('  Data directories and database ready')
"
print_ok "ONYX data structure"

# ── 6. Create .env if missing ────────────────────────────────
print_step "Checking .env configuration"
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "CLAUDE_API_KEY=" > "$ENV_FILE"
    print_ok "Created .env (add your key before launching)"
else
    print_ok ".env already exists"
fi

# ── 7. Create launcher script ────────────────────────────────
print_step "Creating launcher"
LAUNCHER="$INSTALL_DIR/launch_onyx.sh"

cat > "$LAUNCHER" << 'LAUNCHER_SCRIPT'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Check .env
if [ ! -f ".env" ]; then
    zenity --error --text="Missing .env file. Run the installer first." --width=400 2>/dev/null || \
        echo "ERROR: .env file not found."
    exit 1
fi

if ! grep -q "CLAUDE_API_KEY=." .env; then
    zenity --info --text="Add your Claude API key to .env first.\n\n1. Get key: https://console.anthropic.com/\n2. Edit: $SCRIPT_DIR/.env\n3. Set CLAUDE_API_KEY=sk-..." --width=500 2>/dev/null || \
        echo "Please set CLAUDE_API_KEY in .env"
    # Open .env in default editor
    command -v xdg-open &>/dev/null && xdg-open ".env" &
    exit 1
fi

python3 desktop_app/main.py 2>&1 | tee -a Onyx/logs/launch.log
LAUNCHER_SCRIPT

chmod +x "$LAUNCHER"
print_ok "Launcher: $LAUNCHER"

# ── 8. Desktop entry + shortcut ──────────────────────────────
print_step "Creating desktop entry"
ICON_PATH="$INSTALL_DIR/install/onyx_icon.png"
DESKTOP_FILE="$HOME/.local/share/applications/onyx.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << DESKTOP_ENTRY
[Desktop Entry]
Version=1.0
Type=Application
Name=ONYX AI Assistant
Comment=Local AI Chat Assistant with Voice Input
Exec=$LAUNCHER
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Office;Development;
Keywords=AI;Assistant;Chat;Voice;
StartupNotify=true
StartupWMClass=ONYX
DESKTOP_ENTRY

chmod +x "$DESKTOP_FILE"
print_ok "App menu entry created"

if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/ONYX.desktop"
    chmod +x "$HOME/Desktop/ONYX.desktop"
    command -v gio &>/dev/null && gio set "$HOME/Desktop/ONYX.desktop" metadata::trusted true 2>/dev/null || true
    print_ok "Desktop shortcut created"
fi

command -v update-desktop-database &>/dev/null && \
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# ── 9. Quick validation ──────────────────────────────────────
print_step "Validating installation"
python3 -c "
import sys
ok = True
checks = [
    ('PySide6',              'import PySide6'),
    ('emergentintegrations', 'from emergentintegrations.llm.chat import LlmChat'),
    ('pyttsx3 (TTS)',        'import pyttsx3'),
    ('dotenv',               'import dotenv'),
]
for name, stmt in checks:
    try:
        exec(stmt)
        print(f'  [OK] {name}')
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')
        ok = False

# Optional heavy deps (Whisper/Torch)
for name, stmt in [('torch', 'import torch'), ('whisper', 'import whisper'), ('pyaudio', 'import pyaudio')]:
    try:
        exec(stmt)
        print(f'  [OK] {name}')
    except Exception:
        print(f'  [WARN] {name} not installed (voice features will be disabled)')

sys.exit(0 if ok else 1)
"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}=========================================================${NC}"
echo -e "${GREEN}        Installation Complete                            ${NC}"
echo -e "${GREEN}=========================================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Get your Claude API key from https://console.anthropic.com/"
echo "  2. Edit: $ENV_FILE"
echo "     Set: CLAUDE_API_KEY=sk-ant-..."
echo "  3. Launch ONYX:"
echo "     - Click the ONYX icon on your desktop"
echo "     - Or run: $LAUNCHER"
echo ""
echo -e "${BLUE}=========================================================${NC}"
