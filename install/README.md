# ONYX Installation

## Quick Install

### One-Command Installation

```bash
cd /app/install
chmod +x setup.sh
./setup.sh
```

That's it! The script will:
- ✓ Install all system dependencies
- ✓ Install all Python packages
- ✓ Create ONYX icon on desktop
- ✓ Add ONYX to application menu
- ✓ Run tests to verify installation

## After Installation

### Step 1: Get API Key

1. Visit: https://console.anthropic.com/
2. Create an account (or sign in)
3. Generate an API key
4. Copy the key

### Step 2: Add API Key

**Option A - Click to edit:**
- The first time you launch ONYX, it will prompt you
- Click OK and it will open the .env file for you

**Option B - Manual edit:**
```bash
nano /app/.env
```

Add your key:
```
CLAUDE_API_KEY=sk-ant-your-actual-key-here
```

Save and close.

### Step 3: Launch ONYX

**Option A - Desktop Icon:**
- Double-click the "ONYX" icon on your desktop

**Option B - Application Menu:**
- Press Super key (Windows key)
- Type "ONYX"
- Click "ONYX AI Assistant"

**Option C - Command Line:**
```bash
/app/launch_onyx.sh
```

## What Gets Installed

### Desktop Integration
- Desktop icon with futuristic robot
- Application menu entry
- System integration (searchable)

### System Packages
- Qt5 libraries (GUI framework)
- PortAudio (audio input)
- Build tools

### Python Packages  
- PySide6 (Qt for Python)
- PyTorch (~2GB - for Whisper)
- OpenAI Whisper (voice recognition)
- Claude integration
- All dependencies

### Local Data
- `/app/Onyx/` - Your data folder
  - `history/` - Chat database
  - `config/` - Settings & personality
  - `voice/` - Voice recordings
  - `logs/` - Application logs

## Installation Locations

```
/app/                              # Application files
├── desktop_app/                   # ONYX application
├── Onyx/                          # Your data
├── .env                           # API key (you add this)
└── launch_onyx.sh                 # Launcher script

~/Desktop/ONYX.desktop            # Desktop shortcut
~/.local/share/applications/      # App menu entry
```

## Troubleshooting Installation

### "Permission denied" error

```bash
chmod +x /app/install/setup.sh
sudo ./setup.sh
```

### "System packages failed to install"

Try updating package lists first:
```bash
sudo apt-get update
sudo apt-get upgrade
```

Then run setup again.

### "Python packages failed to install"

Try installing to user directory:
```bash
pip3 install --user -r /app/requirements.txt
```

### "Tests failed"

If most tests pass (4-5 out of 6), you can likely still use ONYX.
The API key warning is normal before you add your key.

### Desktop icon doesn't appear

Manually copy:
```bash
cp ~/.local/share/applications/onyx.desktop ~/Desktop/
chmod +x ~/Desktop/ONYX.desktop
```

### Icon shows as generic

Install ImageMagick:
```bash
sudo apt-get install imagemagick
```

Then re-run setup.sh

## Uninstalling

To remove ONYX:

```bash
# Remove desktop files
rm ~/Desktop/ONYX.desktop
rm ~/.local/share/applications/onyx.desktop

# Remove application (WARNING: deletes all chats)
rm -rf /app/desktop_app
rm -rf /app/Onyx

# Remove Python packages (optional)
pip3 uninstall -y PySide6 openai-whisper torch torchaudio PyAudio emergentintegrations
```

## Distribution-Specific Notes

### Ubuntu / Debian
Setup script fully automatic.

### Fedora / RHEL / CentOS
Setup script uses `dnf` automatically.

### Arch / Manjaro
Setup script uses `pacman` automatically.

### Other Distributions
You may need to install Qt5 and PortAudio manually:

```bash
# Install your distro's equivalent of:
- qt5-base / qtbase5-dev
- portaudio / portaudio19-dev
- python3-dev
- build-essential / base-devel
```

Then run setup.sh

## Verification

After installation, verify everything works:

```bash
cd /app
python3 test_onyx.py
```

Should show:
```
🎉 All tests passed! ONYX is ready to run.
```

## Getting Help

1. Check logs: `cat /app/Onyx/logs/onyx_*.log`
2. Run tests: `python3 /app/test_onyx.py`
3. Read docs: `cat /app/README.md`
4. Check install log: `cat /app/install/install.log`

## Manual Installation

If the script doesn't work, follow these steps:

1. **Install system packages:**
   ```bash
   sudo apt-get install qtbase5-dev portaudio19-dev python3-pip
   ```

2. **Install Python packages:**
   ```bash
   cd /app
   pip3 install -r requirements.txt
   ```

3. **Initialize data:**
   ```bash
   python3 -c "from desktop_app.services.storage_service import StorageService; StorageService().initialize()"
   ```

4. **Create launcher:**
   ```bash
   cp /app/run_onyx.sh /app/launch_onyx.sh
   chmod +x /app/launch_onyx.sh
   ```

5. **Add to desktop:**
   ```bash
   cp /app/install/onyx.desktop ~/.local/share/applications/
   cp /app/install/onyx.desktop ~/Desktop/
   ```

6. **Add API key:**
   ```bash
   echo "CLAUDE_API_KEY=your_key" > /app/.env
   ```

7. **Launch:**
   ```bash
   /app/launch_onyx.sh
   ```

---

**Ready to use ONYX!** 🚀
