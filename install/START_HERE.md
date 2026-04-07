```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║            ONYX Desktop AI Assistant Installer                ║
║                                                               ║
║         🤖 One-Click Installation with Desktop Icon 🤖        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🚀 QUICK START

### Run the installer:

```bash
./setup.sh
```

**OR double-click `setup.sh` in your file manager**

That's it! The script does EVERYTHING.

---

## 📋 What Happens Next

### 1️⃣ **Installation (Automatic)**
   - Detects your Linux distribution
   - Installs system packages (Qt5, PortAudio)
   - Installs Python packages (~2GB, 10-30 min)
   - Creates desktop icon with futuristic robot
   - Adds ONYX to application menu
   - Runs tests

### 2️⃣ **Add API Key (You Do This)**
   - Get key: https://console.anthropic.com/
   - Edit: `/app/.env`
   - Add: `CLAUDE_API_KEY=your_key_here`
   
   **OR** just launch ONYX—it will prompt you!

### 3️⃣ **Launch ONYX (Click Icon)**
   - Desktop icon appears automatically
   - Double-click to launch
   - Start chatting with Claude Opus 4.6!

---

## 🖼️ Desktop Icon

Your desktop will get a **futuristic robot icon**:

- 🤖 Robot silhouette with blue accents
- 📡 Antenna with glow effect
- ⚡ Modern dark theme
- 512x512 high-resolution PNG

**Files in this folder:**
- `setup.sh` ← **Run this!**
- `onyx_icon.png` ← Desktop icon (robot)
- `onyx_icon.svg` ← Vector version
- Other documentation files

---

## ⚙️ Installation Details

**Installs:**
- System: Qt5, PortAudio, build tools
- Python: PySide6, PyTorch, Whisper, Claude AI
- Desktop: Icon, menu entry, launcher

**Time:** 10-30 minutes (download dependent)

**Disk Space:** ~3-4GB

**Supported:** Ubuntu, Debian, Fedora, Arch, and more

---

## ✅ Verification

After installation:

```bash
cd /app
python3 test_onyx.py
```

Should show: `🎉 All tests passed! (6/6)`

---

## 🆘 Problems?

### Installer won't run
```bash
chmod +x setup.sh
./setup.sh
```

### Need sudo
```bash
sudo ./setup.sh
```

### Desktop icon missing
```bash
cp ~/.local/share/applications/onyx.desktop ~/Desktop/
chmod +x ~/Desktop/ONYX.desktop
```

---

## 📚 More Help

- **Quick Guide:** `INSTALL_GUIDE.md` (this folder)
- **Full Docs:** `/app/README.md`
- **Quick Start:** `/app/QUICKSTART.md`

---

## ✨ Features

Once installed:

- ✅ Claude Opus 4.6 AI chat
- ✅ Local voice input (Whisper)
- ✅ Chat history saved locally
- ✅ Customizable personality
- ✅ Modern dark UI
- ✅ Desktop icon access

---

## 🎯 Three Steps to Success

1. **Run:** `./setup.sh`
2. **Add:** API key to `.env`
3. **Click:** Desktop icon

**That's it! You're using ONYX!** 🚀

---

```
Questions? Check:
  • INSTALL_GUIDE.md (detailed)
  • /app/README.md (complete docs)
  • /app/Onyx/logs/ (application logs)
```

**Happy chatting with ONYX!** 🤖💙
