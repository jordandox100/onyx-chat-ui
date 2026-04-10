# ONYX Desktop Installation Guide

## 🚀 One-Click Installation

### Step 1: Run Installer

**Option A: Double-click (GUI):**
1. Navigate to `/app/install/` folder
2. Double-click `setup.sh`
3. If prompted, select "Run in Terminal" or "Execute"

**Option B: Terminal:**
```bash
cd /app/install
./setup.sh
```

**Option C: With sudo (if needed):**
```bash
cd /app/install
sudo ./setup.sh
```

### What the Installer Does

The installer will automatically:

1. ✅ **Detect your Linux distribution**
   - Ubuntu, Debian, Fedora, Arch, etc.

2. ✅ **Install system packages**
   - Qt5 libraries (GUI framework)
   - PortAudio (microphone support)
   - Build tools

3. ✅ **Install Python packages**
   - PySide6 (GUI)
   - PyTorch (~2GB)
   - Whisper (voice recognition)
   - Claude AI integration
   - ~10-30 minutes download time

4. ✅ **Create desktop icon**
   - Futuristic robot icon
   - Appears on desktop
   - Added to application menu

5. ✅ **Run tests**
   - Verifies installation
   - All systems working

### Step 2: Add API Key

After installation:

1. **Get your API key:**
   - Visit: https://console.anthropic.com/
   - Sign up or log in
   - Go to API Keys section
   - Click "Create Key"
   - Copy the key (starts with `sk-ant-`)

2. **Add to ONYX:**
   - First launch will prompt you
   - OR edit `/app/.env` manually:
   ```bash
   nano /app/.env
   ```
   Add:
   ```
   CLAUDE_API_KEY=sk-ant-your-actual-key-here
   ```
   Save (Ctrl+O, Enter, Ctrl+X)

### Step 3: Launch ONYX

**Option A: Desktop Icon** (Easiest)
- Double-click the "ONYX" icon on your desktop

**Option B: Application Menu**
- Press Super/Windows key
- Type "ONYX"
- Click "ONYX AI Assistant"

**Option C: Command Line**
```bash
/app/launch_onyx.sh
```

---

## 📦 What Gets Installed

### Desktop Integration

```
~/Desktop/ONYX.desktop              # Desktop shortcut
~/.local/share/applications/        # App menu entry
  └── onyx.desktop
```

**Icon Features:**
- 🤖 Futuristic robot silhouette
- 🔵 Blue accent color (#4a9eff)
- ✨ Animated elements (in SVG version)
- 💻 Modern dark theme

### Application Files

```
/app/
├── desktop_app/           # ONYX application
├── Onyx/                  # Your data (created on first run)
├── .env                   # API key configuration
├── launch_onyx.sh         # Launcher script
└── install/
    ├── setup.sh           # Installer
    ├── onyx_icon.png      # Desktop icon
    └── onyx_icon.svg      # Vector icon
```

### System Packages

**Ubuntu/Debian:**
- qtbase5-dev
- portaudio19-dev
- python3-dev
- build-essential

**Fedora/RHEL:**
- qt5-qtbase-devel
- portaudio-devel
- python3-devel
- gcc, gcc-c++

**Arch/Manjaro:**
- qt5-base
- portaudio
- python
- base-devel

### Python Packages

- **PySide6** - Qt GUI framework
- **torch** - PyTorch (~2GB)
- **torchaudio** - Audio processing
- **openai-whisper** - Voice-to-text
- **anthropic** - Claude AI SDK
- **PyAudio** - Microphone input
- **python-dotenv** - Configuration

---

## 📖 Using ONYX

### First Launch

1. **Desktop Icon** appears after installation
2. **Double-click** the ONYX icon
3. If API key not set:
   - Dialog appears
   - .env file opens automatically
   - Add your key
   - Save and relaunch

### Normal Usage

1. **Click desktop icon** or search "ONYX"
2. Window opens with sidebar
3. Click **"+ New Chat"**
4. Type message and press **Send**
5. AI responds using **Claude Sonnet 4.6** (default, switchable)

### Voice Input

1. Click **🎤 microphone button**
2. Speak for up to 5 seconds
3. Button turns red while recording
4. Text appears in input box
5. Edit if needed, then send

---

## ⚙️ Configuration

### API Key Location

```bash
/app/.env
```

Content:
```bash
CLAUDE_API_KEY=sk-ant-your-key-here
```

### Personality Configuration

```bash
/app/Onyx/config/personality.txt
```

Edit this file to change how ONYX responds.
Restart ONYX after editing.

### Data Storage

```
/app/Onyx/
├── history/
│   └── chats.db          # Your conversations
├── config/
│   └── personality.txt   # AI personality
├── voice/                # Voice recordings
└── logs/                 # Application logs
```

---

## 🔧 Troubleshooting

### Installation Issues

#### "Permission denied"
```bash
cd /app/install
chmod +x setup.sh
sudo ./setup.sh
```

#### "System packages failed"
```bash
# Update package lists first
sudo apt-get update
sudo apt-get upgrade

# Then retry
./setup.sh
```

#### "Python packages failed"
```bash
# Install to user directory
cd /app
pip3 install --user -r requirements.txt
```

#### "Tests failed"
Most common: API key warning (normal before adding key)
If 5/6 tests pass, installation is OK.

### Desktop Icon Issues

#### Icon doesn't appear
```bash
# Manually copy
cp ~/.local/share/applications/onyx.desktop ~/Desktop/
chmod +x ~/Desktop/ONYX.desktop

# Mark as trusted (Ubuntu)
gio set ~/Desktop/ONYX.desktop metadata::trusted true
```

#### Icon shows generic image
```bash
# Install ImageMagick
sudo apt-get install imagemagick

# Re-run installer
cd /app/install
./setup.sh
```

### Launch Issues

#### "CLAUDE_API_KEY not found"
1. Edit: `/app/.env`
2. Add: `CLAUDE_API_KEY=your_key`
3. Save and relaunch

#### "Qt platform plugin error"
```bash
export QT_QPA_PLATFORM=xcb
/app/launch_onyx.sh
```

#### Window doesn't open
Check logs:
```bash
cat /app/Onyx/logs/onyx_*.log
cat /app/Onyx/logs/launch.log
```

### Voice Input Issues

#### Microphone doesn't work
```bash
# Test microphone
arecord -l

# Reinstall audio support
sudo apt-get install --reinstall portaudio19-dev
pip3 install --force-reinstall PyAudio
```

#### "No module named 'whisper'"
```bash
pip3 install openai-whisper torch torchaudio
```

---

## 📦 Updating ONYX

To update to a new version:

```bash
# Backup your data
cp -r /app/Onyx ~/onyx_backup

# Download new version
cd /app
git pull  # If using git

# Re-run installer
cd install
./setup.sh

# Your data in Onyx/ folder is preserved
```

---

## 🗑️ Uninstalling

### Remove ONYX

```bash
# Remove desktop files
rm ~/Desktop/ONYX.desktop
rm ~/.local/share/applications/onyx.desktop

# Remove application
rm -rf /app/desktop_app
rm -rf /app/install

# Remove data (WARNING: Deletes all chats)
rm -rf /app/Onyx

# Remove Python packages (optional)
pip3 uninstall -y PySide6 openai-whisper torch torchaudio PyAudio anthropic piper-tts
```

### Keep Your Data

To remove ONYX but keep your chats:

```bash
# Backup first
cp -r /app/Onyx ~/onyx_backup

# Then uninstall as above
```

To restore later:
```bash
cp -r ~/onyx_backup /app/Onyx
```

---

## 📊 Verification

### Test Installation

```bash
cd /app
python3 test_onyx.py
```

**Expected output:**
```
🎉 All tests passed! ONYX is ready to run.
Results: 6/6 tests passed
```

### Verify Desktop Integration

```bash
# Check desktop file
ls -lh ~/Desktop/ONYX.desktop

# Check app menu entry
ls -lh ~/.local/share/applications/onyx.desktop

# Check icon
ls -lh /app/install/onyx_icon.png
```

### Verify API Connection

1. Launch ONYX
2. Create new chat
3. Send message: "Say hi"
4. Should receive response from Claude Opus 4.6

---

## 📚 Additional Resources

- **Full Documentation:** `/app/README.md`
- **Quick Start:** `/app/QUICKSTART.md`
- **Deployment Guide:** `/app/DEPLOYMENT.md`
- **Project Structure:** `/app/PROJECT_STRUCTURE.md`

---

## ❓ Getting Help

1. **Check logs:**
   ```bash
   tail -n 50 /app/Onyx/logs/onyx_*.log
   ```

2. **Run tests:**
   ```bash
   python3 /app/test_onyx.py
   ```

3. **Verify dependencies:**
   ```bash
   pip3 list | grep -E 'PySide6|torch|whisper'
   ```

4. **Check display:**
   ```bash
   echo $DISPLAY
   xdpyinfo | head -n 5
   ```

---

## ✅ Installation Checklist

- [ ] Ran `/app/install/setup.sh`
- [ ] All tests passed (6/6)
- [ ] Desktop icon appears
- [ ] App menu entry exists
- [ ] Got Claude API key
- [ ] Added key to `.env` file
- [ ] Launched ONYX successfully
- [ ] Sent test message
- [ ] Received AI response
- [ ] Voice input works (optional)

---

**Enjoy using ONYX!** 🤖
