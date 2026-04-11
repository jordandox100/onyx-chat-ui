#!/bin/bash
########################################
#  ONYX AI Assistant — One-Click Setup #
#  Run this. That's it.                #
########################################

set -e

R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
C='\033[0;36m'
B='\033[1;37m'
N='\033[0m'

clear
echo -e "${C}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║         ONYX  AI  ASSISTANT           ║"
echo "  ║            installer                  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${N}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
VENV="$SCRIPT_DIR/.venv"

fail() { echo -e "${R}ERROR: $1${N}"; exit 1; }
ok()   { echo -e "  ${G}+${N} $1"; }
step() { echo -e "\n${C}[$1]${N} $2"; }

# ─── Python check ─────────────────────────────
step 1 "Checking Python..."
command -v python3 &>/dev/null || fail "python3 not found. Install Python 3.10+ first."
PY_VER=$(python3 -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}')")
PY_MAJOR=${PY_VER%%.*}
PY_MINOR=${PY_VER##*.}
[ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ] || fail "Python 3.10+ required (found $PY_VER)"
ok "Python $PY_VER"

# ─── System packages ─────────────────────────
step 2 "Installing system dependencies..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
        ubuntu|debian|pop|linuxmint|zorin)
            sudo apt-get update -qq 2>/dev/null
            sudo apt-get install -y -qq python3-venv python3-dev portaudio19-dev \
                espeak-ng libxcb-xinerama0 libxcb-cursor0 build-essential 2>/dev/null
            ;;
        fedora|rhel|centos|rocky|alma)
            sudo dnf install -y python3-devel portaudio-devel espeak-ng gcc gcc-c++ 2>/dev/null
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm --needed python portaudio espeak-ng base-devel 2>/dev/null
            ;;
        *)
            echo -e "  ${Y}Unknown distro ($ID). You may need: portaudio, espeak-ng, python3-venv${N}"
            ;;
    esac
fi
ok "System packages ready"

# ─── Virtual environment ─────────────────────
step 3 "Setting up Python environment..."
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --upgrade pip -q 2>/dev/null
ok "Virtual environment ready"

# ─── Python packages ─────────────────────────
step 4 "Installing Python packages (this may take a few minutes)..."
pip install -r "$SCRIPT_DIR/requirements.txt" -q 2>&1 | tail -3
ok "All packages installed"

# ─── TTS voice models ────────────────────────
step 5 "Downloading TTS voice models..."
VOICES="$SCRIPT_DIR/Onyx/voices"
mkdir -p "$VOICES"
HF="https://huggingface.co/rhasspy/piper-voices/resolve/main"

grab() {
    local lang="$1" name="$2" q="$3"
    local prefix="${lang##*/}-${name}-${q}"
    local remote="${lang}/${name}/${q}"
    [ -f "$VOICES/${prefix}.onnx" ] && { ok "$prefix (cached)"; return; }
    echo -e "  ${Y}downloading ${prefix}...${N}"
    curl -sL "$HF/${remote}/${prefix}.onnx" -o "$VOICES/${prefix}.onnx"
    curl -sL "$HF/${remote}/${prefix}.onnx.json" -o "$VOICES/${prefix}.onnx.json"
    ok "$prefix"
}

grab "en/en_GB" "alan"                  "medium"
grab "en/en_GB" "northern_english_male" "medium"
grab "en/en_GB" "semaine"               "medium"
grab "en/en_GB" "aru"                   "medium"
grab "en/en_US" "ryan"                  "medium"

# ─── Data folders ─────────────────────────────
step 6 "Initializing ONYX..."
python3 -c "
import sys; sys.path.insert(0,'$SCRIPT_DIR')
from desktop_app.services.storage_service import StorageService
StorageService().initialize()
" 2>/dev/null
ok "Data folders and database ready"

# ─── API Key ──────────────────────────────────
step 7 "API Key setup"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ] && grep -q "CLAUDE_API_KEY=." "$ENV_FILE" 2>/dev/null; then
    ok "API key already configured"
else
    echo ""
    echo -e "${B}  ONYX needs a Claude API key to work.${N}"
    echo -e "  Get one at: ${C}https://console.anthropic.com/${N}"
    echo ""
    read -rp "  Paste your Claude API key (or press Enter to skip): " API_KEY
    echo ""

    if [ -n "$API_KEY" ]; then
        echo "CLAUDE_API_KEY=$API_KEY" > "$ENV_FILE"
        ok "API key saved to .env"
    else
        echo "CLAUDE_API_KEY=" > "$ENV_FILE"
        echo -e "  ${Y}Skipped. Edit $ENV_FILE later before launching.${N}"
    fi
fi

# ─── Desktop shortcut ────────────────────────
step 8 "Creating desktop launcher..."

LAUNCHER="$SCRIPT_DIR/launch_onyx.sh"
cat > "$LAUNCHER" << LAUNCH
#!/bin/bash
cd "$SCRIPT_DIR"
source "$VENV/bin/activate"
python3 desktop_app/main.py 2>&1 | tee -a Onyx/logs/launch.log
LAUNCH
chmod +x "$LAUNCHER"

ICON="$SCRIPT_DIR/install/onyx_icon.png"
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/onyx.desktop" << DESK
[Desktop Entry]
Version=1.0
Type=Application
Name=ONYX AI Assistant
Comment=Local AI Chat Assistant
Exec=$LAUNCHER
Icon=$ICON
Terminal=false
Categories=Utility;Development;
StartupNotify=true
DESK
chmod +x "$DESKTOP_DIR/onyx.desktop"

if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_DIR/onyx.desktop" "$HOME/Desktop/ONYX.desktop"
    chmod +x "$HOME/Desktop/ONYX.desktop"
    command -v gio &>/dev/null && gio set "$HOME/Desktop/ONYX.desktop" metadata::trusted true 2>/dev/null || true
fi
ok "Desktop shortcut created"

# ─── Done ─────────────────────────────────────
echo ""
echo -e "${G}  ╔═══════════════════════════════════════╗"
echo -e "  ║       ONYX is installed and ready      ║"
echo -e "  ╚═══════════════════════════════════════╝${N}"
echo ""

# ─── Launch ──────────────────────────────────
if grep -q "CLAUDE_API_KEY=." "$ENV_FILE" 2>/dev/null; then
    read -rp "  Launch ONYX now? [Y/n] " LAUNCH_NOW
    if [ "$LAUNCH_NOW" != "n" ] && [ "$LAUNCH_NOW" != "N" ]; then
        echo -e "\n  ${C}Starting ONYX...${N}\n"
        exec "$LAUNCHER"
    else
        echo -e "\n  Run ${C}./launch_onyx.sh${N} or click the desktop icon anytime.\n"
    fi
else
    echo -e "  ${Y}Add your API key to .env, then run:${N}"
    echo -e "  ${C}./launch_onyx.sh${N}"
    echo ""
fi
