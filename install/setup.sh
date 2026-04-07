#!/bin/bash

##############################################
# ONYX Desktop AI Assistant - Installation  #
# Automated setup script for Linux          #
##############################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════"
echo "        ONYX Desktop AI Assistant Installer          "
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"

# Get the absolute path of the installation directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${GREEN}Installation directory: ${INSTALL_DIR}${NC}\n"

# Check if running as root (needed for system packages)
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Note: This script needs sudo privileges to install system packages.${NC}"
    echo -e "${YELLOW}You will be prompted for your password.${NC}\n"
fi

# Function to print step
print_step() {
    echo -e "\n${BLUE}═══ $1 ═══${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Detect Linux distribution
print_step "Detecting Linux Distribution"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    print_success "Detected: $NAME $VERSION"
else
    print_error "Cannot detect Linux distribution"
    OS="unknown"
fi

# Check Python version
print_step "Checking Python Version"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.11 or higher
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
        print_warning "Python 3.11+ is recommended (you have $PYTHON_VERSION)"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    print_error "Python 3 not found!"
    echo "Please install Python 3.11 or higher first."
    exit 1
fi

# Check pip
print_step "Checking pip"
if command -v pip3 &> /dev/null; then
    print_success "pip3 found"
else
    print_error "pip3 not found!"
    echo "Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Install system dependencies
print_step "Installing System Dependencies"
echo "This will install: Qt5, PortAudio, and build tools"

case $OS in
    ubuntu|debian)
        print_success "Installing for Debian/Ubuntu..."
        sudo apt-get update
        sudo apt-get install -y \
            qtbase5-dev \
            qt5-qmake \
            libqt5widgets5 \
            libqt5gui5 \
            libqt5core5a \
            portaudio19-dev \
            python3-dev \
            python3-pip \
            build-essential \
            libxcb-xinerama0 \
            libxcb-cursor0 || {
                print_error "Failed to install system packages"
                exit 1
            }
        print_success "System packages installed"
        ;;
    
    fedora|rhel|centos)
        print_success "Installing for Fedora/RHEL/CentOS..."
        sudo dnf install -y \
            qt5-qtbase-devel \
            portaudio-devel \
            python3-devel \
            gcc \
            gcc-c++ || {
                print_error "Failed to install system packages"
                exit 1
            }
        print_success "System packages installed"
        ;;
    
    arch|manjaro)
        print_success "Installing for Arch/Manjaro..."
        sudo pacman -S --noconfirm \
            qt5-base \
            portaudio \
            python \
            python-pip \
            base-devel || {
                print_error "Failed to install system packages"
                exit 1
            }
        print_success "System packages installed"
        ;;
    
    *)
        print_warning "Unknown distribution. Attempting generic installation..."
        print_warning "You may need to install Qt5 and PortAudio manually."
        ;;
esac

# Install Python packages
print_step "Installing Python Packages"
echo "This will download ~2GB of packages (PyTorch, Whisper, etc.)"
echo "This may take 10-30 minutes depending on your internet speed."
echo ""
read -p "Continue? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_warning "Installation cancelled"
    exit 1
fi

cd "$INSTALL_DIR"

# Upgrade pip first
echo "Upgrading pip..."
pip3 install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip3 install -r requirements.txt || {
    print_error "Failed to install Python packages"
    print_warning "Try: pip3 install --user -r requirements.txt"
    exit 1
}

print_success "Python packages installed"

# Initialize ONYX data structure
print_step "Initializing ONYX Data Structure"
cd "$INSTALL_DIR"
python3 -c "
from desktop_app.services.storage_service import StorageService
storage = StorageService()
storage.initialize()
print('✓ ONYX initialized')
" || {
    print_error "Failed to initialize ONYX"
    exit 1
}
print_success "Data structure created"

# Create launcher script
print_step "Creating Launcher Script"
LAUNCHER="$INSTALL_DIR/launch_onyx.sh"

cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash

# ONYX Launcher - Checks for API key and launches application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    zenity --error --text="Configuration file (.env) not found!\n\nPlease run the installer first." --width=400 2>/dev/null || \
    xmessage -center "Configuration file (.env) not found! Please run the installer first." &
    exit 1
fi

# Check if API key is set
if ! grep -q "CLAUDE_API_KEY=." .env; then
    zenity --info --text="Welcome to ONYX!\n\nPlease add your Claude API key to the .env file:\n\n1. Get your key from: https://console.anthropic.com/\n2. Edit the .env file\n3. Add: CLAUDE_API_KEY=your_key_here\n4. Save and launch ONYX again" --width=500 2>/dev/null || \
    xmessage -center "Please add your CLAUDE_API_KEY to the .env file. Visit https://console.anthropic.com/ to get your key." &
    
    # Try to open the .env file in default editor
    if command -v xdg-open &> /dev/null; then
        xdg-open ".env" &
    elif command -v gedit &> /dev/null; then
        gedit ".env" &
    elif command -v kate &> /dev/null; then
        kate ".env" &
    elif command -v nano &> /dev/null; then
        x-terminal-emulator -e nano ".env" &
    fi
    exit 1
fi

# Launch ONYX
python3 desktop_app/main.py 2>&1 | tee -a Onyx/logs/launch.log

LAUNCHER_EOF

chmod +x "$LAUNCHER"
print_success "Launcher script created"

# Download/Create icon
print_step "Creating Application Icon"
ICON_PATH="$INSTALL_DIR/install/onyx_icon.png"

# Create a simple SVG and convert to PNG if ImageMagick is available
if command -v convert &> /dev/null; then
    # Create SVG
    cat > /tmp/onyx_icon.svg << 'SVG_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="512" height="512" rx="80" fill="#0a0a0a"/>
  
  <!-- Outer glow -->
  <circle cx="256" cy="256" r="180" fill="#1a1a2e" opacity="0.5"/>
  
  <!-- Robot head -->
  <rect x="180" y="180" width="152" height="152" rx="20" fill="#16213e" stroke="#4a9eff" stroke-width="4"/>
  
  <!-- Eyes -->
  <circle cx="220" cy="230" r="15" fill="#4a9eff">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="292" cy="230" r="15" fill="#4a9eff">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Antenna -->
  <line x1="256" y1="180" x2="256" x2="140" stroke="#4a9eff" stroke-width="3"/>
  <circle cx="256" cy="140" r="8" fill="#4a9eff">
    <animate attributeName="r" values="8;12;8" dur="1.5s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Mouth/speaker -->
  <rect x="210" y="280" width="92" height="30" rx="15" fill="#0f3460" stroke="#4a9eff" stroke-width="2"/>
  <line x1="225" y1="285" x2="225" y2="305" stroke="#4a9eff" stroke-width="2"/>
  <line x1="240" y1="285" x2="240" y2="305" stroke="#4a9eff" stroke-width="2"/>
  <line x1="255" y1="285" x2="255" y2="305" stroke="#4a9eff" stroke-width="2"/>
  <line x1="270" y1="285" x2="270" y2="305" stroke="#4a9eff" stroke-width="2"/>
  <line x1="285" y1="285" x2="285" y2="305" stroke="#4a9eff" stroke-width="2"/>
  
  <!-- Text -->
  <text x="256" y="400" font-family="Arial, sans-serif" font-size="48" font-weight="bold" 
        fill="#4a9eff" text-anchor="middle">ONYX</text>
</svg>
SVG_EOF

    convert -background none /tmp/onyx_icon.svg "$ICON_PATH" 2>/dev/null && \
        print_success "Icon created" || \
        print_warning "Could not create PNG icon, using SVG"
    rm -f /tmp/onyx_icon.svg
else
    print_warning "ImageMagick not found, creating text-based icon"
    # Create a simple colored square as fallback
    if command -v convert &> /dev/null; then
        convert -size 512x512 xc:"#0a0a0a" -fill "#4a9eff" -pointsize 120 -gravity center \
            -annotate +0+0 "ONYX" "$ICON_PATH" 2>/dev/null || touch "$ICON_PATH"
    else
        # Just create an empty file, desktop entry will use default icon
        touch "$ICON_PATH"
    fi
fi

# Create desktop entry
print_step "Creating Desktop Entry"
DESKTOP_FILE="$HOME/.local/share/applications/onyx.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << DESKTOP_EOF
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
DESKTOP_EOF

chmod +x "$DESKTOP_FILE"
print_success "Desktop entry created"

# Also create desktop shortcut
print_step "Creating Desktop Shortcut"
if [ -d "$HOME/Desktop" ]; then
    DESKTOP_SHORTCUT="$HOME/Desktop/ONYX.desktop"
    cp "$DESKTOP_FILE" "$DESKTOP_SHORTCUT"
    chmod +x "$DESKTOP_SHORTCUT"
    
    # Mark as trusted for some desktop environments
    if command -v gio &> /dev/null; then
        gio set "$DESKTOP_SHORTCUT" metadata::trusted true 2>/dev/null || true
    fi
    
    print_success "Desktop shortcut created"
else
    print_warning "Desktop folder not found, skipping desktop shortcut"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    print_success "Desktop database updated"
fi

# Run tests
print_step "Running Tests"
cd "$INSTALL_DIR"
python3 test_onyx.py

TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    print_success "All tests passed!"
else
    print_warning "Some tests failed, but installation completed"
fi

# Final summary
echo -e "\n${GREEN}"
echo "═══════════════════════════════════════════════════════"
echo "        Installation Complete! 🎉                    "
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Get your Claude API key:${NC}"
echo "   Visit: https://console.anthropic.com/"
echo "   Create an account and generate an API key"
echo ""
echo -e "${YELLOW}2. Add your API key:${NC}"
echo "   Edit: $INSTALL_DIR/.env"
echo "   Add line: CLAUDE_API_KEY=your_key_here"
echo ""
echo -e "${YELLOW}3. Launch ONYX:${NC}"
echo "   • Click the ONYX icon on your desktop"
echo "   • OR search for 'ONYX' in your application menu"
echo "   • OR run: $LAUNCHER"
echo ""
echo -e "${GREEN}Desktop icon location:${NC} ~/Desktop/ONYX.desktop"
echo -e "${GREEN}App menu entry:${NC} Search for 'ONYX AI Assistant'"
echo -e "${GREEN}Documentation:${NC} $INSTALL_DIR/README.md"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
