# ONYX Desktop Installation - Complete Guide

## \u2728 Installation Overview

ONYX now includes a **one-click installation system** that handles everything automatically.

---

## \ud83d\ude80 Quick Installation (3 Steps)

### Step 1: Run Installer

```bash
cd /app/install
./setup.sh
```

**OR double-click `setup.sh` in your file manager**

The installer will:
- \u2705 Install all system packages (Qt5, PortAudio)
- \u2705 Install all Python packages (~2GB download)
- \u2705 Create desktop icon with futuristic robot
- \u2705 Add ONYX to application menu
- \u2705 Run tests to verify everything works

**Time:** 10-30 minutes (depending on internet speed)

---

### Step 2: Add API Key

After installation:

1. Get your key: https://console.anthropic.com/
2. Edit `/app/.env`:
   ```bash
   CLAUDE_API_KEY=sk-ant-your-key-here
   ```

**OR** just launch ONYX and it will prompt you!

---

### Step 3: Launch ONYX

**Option A:** Double-click desktop icon \ud83d\udda5\ufe0f

**Option B:** Search \"ONYX\" in app menu \ud83d\udd0d

**Option C:** Run `/app/launch_onyx.sh` \ud83d\udcbb

---

## \ud83e\udd16 Desktop Icon

The installer creates a futuristic robot icon:

**Features:**
- \ud83d\udd35 Blue accent colors (#4a9eff)
- \ud83e\udd16 Robot silhouette with animated eyes
- \ud83d\udce1 Antenna with glow effect
- \u26a1 Modern dark theme background
- \u2728 High-resolution (512x512 PNG)

**Locations:**
- Desktop: `~/Desktop/ONYX.desktop`
- App Menu: `~/.local/share/applications/onyx.desktop`
- Icon File: `/app/install/onyx_icon.png`

---

## \ud83d\udcbb What the Installer Does

### System Packages Installed

**Debian/Ubuntu:**
```bash\nqtbase5-dev\nportaudio19-dev\npython3-dev\nbuild-essential\nlibxcb-xinerama0\nlibxcb-cursor0\n```

**Fedora/RHEL:**
```bash\nqt5-qtbase-devel\nportaudio-devel\npython3-devel\ngcc, gcc-c++\n```

**Arch/Manjaro:**
```bash\nqt5-base\nportaudio\nbase-devel\n```

### Python Packages Installed

- **PySide6** - Qt GUI framework
- **anthropic** - Claude AI (Opus 4.6)
- **torch + torchaudio** - PyTorch (~2GB)
- **openai-whisper** - Local voice recognition
- **PyAudio** - Microphone input
- **python-dotenv** - Configuration management
- **aiohttp** - Async HTTP client

### Desktop Integration

1. **Desktop Icon** - Clickable shortcut on desktop
2. **Application Menu** - Searchable in system apps
3. **Launcher Script** - Smart launcher with API key check
4. **Auto-start** - Ready to use immediately

---

## \ud83c\udfae Using ONYX

### First Launch

1. Double-click ONYX desktop icon
2. If no API key:
   - Dialog appears
   - .env file opens automatically
   - Add your key
   - Save and relaunch

3. Window opens with:
   - Left sidebar for chat management
   - Main chat area in center
   - Modern dark theme

### Creating Chats

1. Click **\"+ New Chat\"** button
2. Type message in input box
3. Press **Send** or hit Enter
4. **Claude Opus 4.6** responds
5. Chat auto-saves to local database

### Voice Input

1. Click **\ud83c\udfa4 microphone button**
2. Speak clearly (up to 5 seconds)
3. Button turns red while recording
4. **Local Whisper** transcribes
5. Text appears in input box
6. Edit if needed, then send

### Managing Chats

- **Switch:** Click any chat in sidebar
- **Rename:** Select chat → Click \"Rename\"
- **Delete:** Select chat → Click \"Delete\"
- **History:** All chats persist locally

---

## \u2699\ufe0f AI Model Configuration

**Current Model:** Claude Opus 4.6

**Location:** `/app/desktop_app/services/chat_service.py` (Line 33)

```python\nself.llm_chat.with_model(\"anthropic\", \"claude-opus-4-6\")\n```

**Verified:** \u2705 Using Claude Opus 4.6

### Change Model (Optional)

To use a different model:

```python\n# Claude Sonnet (cheaper, faster)\nself.llm_chat.with_model(\"anthropic\", \"claude-sonnet-4-6\")\n\n# Claude Haiku (cheapest, fastest)\nself.llm_chat.with_model(\"anthropic\", \"claude-haiku-4-5-20251001\")\n```

---

## \ud83d\udcbe Data Storage

All data stored locally in:

```\n/app/Onyx/\n\u251c\u2500\u2500 history/\n\u2502   \u2514\u2500\u2500 chats.db              # SQLite database\n\u251c\u2500\u2500 config/\n\u2502   \u2514\u2500\u2500 personality.txt       # AI personality\n\u251c\u2500\u2500 voice/                    # Voice recordings\n\u2514\u2500\u2500 logs/\n    \u2514\u2500\u2500 onyx_YYYYMMDD.log     # Application logs\n```\n\n**Privacy:** All chats stay on your machine. Nothing sent to cloud except AI API calls.\n\n---\n## \ud83d\udd27 Troubleshooting\n\n### Installation Fails\n\n**Problem:** System packages won't install\n\n**Solution:**\n```bash\nsudo apt-get update\nsudo apt-get upgrade\ncd /app/install\nsudo ./setup.sh\n```\n\n### Desktop Icon Missing\n\n**Problem:** Icon doesn't appear on desktop\n\n**Solution:**\n```bash\ncp ~/.local/share/applications/onyx.desktop ~/Desktop/\nchmod +x ~/Desktop/ONYX.desktop\ngio set ~/Desktop/ONYX.desktop metadata::trusted true\n```\n\n### API Key Not Working\n\n**Problem:** \"CLAUDE_API_KEY not found\" error\n\n**Solution:**\n1. Check file exists: `ls -la /app/.env`\n2. Check content: `cat /app/.env`\n3. Should show: `CLAUDE_API_KEY=sk-ant-...`\n4. No spaces around `=`\n5. No quotes around key\n6. Save and relaunch\n\n### Voice Not Working\n\n**Problem:** Microphone button does nothing\n\n**Solution:**\n```bash\n# Test microphone\narecord -l\n\n# Reinstall audio\nsudo apt-get install --reinstall portaudio19-dev\npip3 install --force-reinstall PyAudio\n```\n\n### Window Won't Open\n\n**Problem:** Nothing happens when clicking icon\n\n**Solution:**\n```bash\n# Check logs\ncat /app/Onyx/logs/onyx_*.log\n\n# Try terminal\nexport QT_QPA_PLATFORM=xcb\n/app/launch_onyx.sh\n```\n\n---\n\n## \u2705 Verification\n\n### Test Installation\n\n```bash\ncd /app\npython3 test_onyx.py\n```\n\n**Expected:**\n```\n\ud83c\udf89 All tests passed! ONYX is ready to run.\nResults: 6/6 tests passed\n```\n\n### Test Desktop Integration\n\n```bash\n# Check files exist\nls ~/Desktop/ONYX.desktop\nls ~/.local/share/applications/onyx.desktop\nls /app/install/onyx_icon.png\n\n# Verify launcher\n/app/launch_onyx.sh\n```\n\n### Test AI Connection\n\n1. Launch ONYX\n2. Create new chat\n3. Send: \"Say hi in one sentence\"\n4. Should get response from Claude Opus 4.6\n\n---\n\n## \ud83d\udcca Installation Checklist\n\n- [ ] Ran `/app/install/setup.sh`\n- [ ] System packages installed\n- [ ] Python packages installed (~2GB)\n- [ ] All tests passed (6/6)\n- [ ] Desktop icon appears\n- [ ] App menu entry exists\n- [ ] Got Claude API key from console.anthropic.com\n- [ ] Added key to `/app/.env`\n- [ ] Launched ONYX (double-click icon)\n- [ ] Window opens successfully\n- [ ] Created first chat\n- [ ] Sent test message\n- [ ] Received AI response\n- [ ] Voice input works (optional)\n\n---\n\n## \ud83d\udcda Documentation\n\n**Installation:**\n- `/app/install/INSTALL_GUIDE.md` - Detailed install guide\n- `/app/install/README.md` - Quick reference\n- `/app/QUICKSTART.md` - 5-minute quick start\n\n**Usage:**\n- `/app/README.md` - Complete documentation\n- `/app/DEPLOYMENT.md` - Deployment options\n- `/app/PROJECT_STRUCTURE.md` - Code structure\n\n**Testing:**\n- `/app/test_onyx.py` - Automated tests\n\n---\n\n## \ud83c\udd98 Support\n\n**Logs:**\n```bash\ntail -50 /app/Onyx/logs/onyx_*.log\n```\n\n**Tests:**\n```bash\npython3 /app/test_onyx.py\n```\n\n**Dependencies:**\n```bash\npip3 list | grep -E 'PySide|torch|whisper|emergent'\n```\n\n**Display:**\n```bash\necho $DISPLAY\nxdpyinfo | head\n```\n\n---\n\n## \ud83c\udf89 Success!\n\nIf all checks pass:\n\n\u2705 **ONYX is installed**\n\u2705 **Desktop icon ready**\n\u2705 **Claude Opus 4.6 active**\n\u2705 **Voice input available**\n\u2705 **Ready to use!**\n\n**Launch ONYX from your desktop and start chatting!** \ud83e\udd16\n\n---\n\n## \ud83d\udd17 Quick Links\n\n- **Claude Console:** https://console.anthropic.com/\n- **Icon Location:** `/app/install/onyx_icon.png`\n- **Launcher:** `/app/launch_onyx.sh`\n- **Config:** `/app/.env`\n- **Data:** `/app/Onyx/`\n\n---\n\n**Enjoy your local AI assistant!** \u2728\n