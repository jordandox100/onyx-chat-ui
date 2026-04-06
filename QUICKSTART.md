# ONYX Quick Start Guide

## \ud83d\ude80 Get Started in 5 Minutes

### Step 1: System Dependencies (2 min)

```bash
sudo apt-get update
sudo apt-get install -y qtbase5-dev portaudio19-dev
```

### Step 2: Python Packages (3-5 min)

```bash
cd /app
pip install -r requirements.txt
```

**Note**: First installation downloads ~2GB of dependencies.

### Step 3: API Key (1 min)

1. Get API key from: https://console.anthropic.com/
2. Edit `.env` file:
   ```bash
   nano .env
   ```
3. Add your key:
   ```
   CLAUDE_API_KEY=sk-ant-your-actual-key-here
   ```

### Step 4: Run ONYX

```bash
python3 desktop_app/main.py
```

**OR**

```bash
chmod +x run_onyx.sh
./run_onyx.sh
```

## \ud83c\udfae Using ONYX

### First Time

1. Window opens with empty sidebar
2. Click **"+ New Chat"**
3. Type a message
4. Press **Send** or hit Enter
5. Wait for AI response

### Voice Input

1. Click the **\ud83c\udfa4 microphone button**
2. Speak clearly for up to 5 seconds
3. Button turns red while recording
4. Transcription appears in input box
5. Edit and send

### Managing Chats

- **Switch chats**: Click any chat in sidebar
- **Rename**: Select chat → **Rename** button
- **Delete**: Select chat → **Delete** button

## \u2699\ufe0f Configuration

### Change AI Personality

Edit the personality file:

```bash
nano Onyx/config/personality.txt
```

Restart ONYX to apply changes.

### Change Whisper Model

Edit `desktop_app/services/voice_service.py`:

```python
# Line 34, change "base" to:
self.whisper_model = whisper.load_model("tiny")   # Fastest
self.whisper_model = whisper.load_model("small")  # Better
self.whisper_model = whisper.load_model("large")  # Best
```

## \u26a1 Performance Tips

### Faster Voice Input
Use tiny Whisper model (see above)

### Lower Costs
Use Claude Sonnet instead of Opus:
```python
# In desktop_app/services/chat_service.py, line 33:
self.llm_chat.with_model("anthropic", "claude-sonnet-4-6")
```

### More RAM Available
Close unused applications before running

## \u2753 Common Issues

### "Qt platform plugin could not be initialized"

**Fix**:
```bash
export QT_QPA_PLATFORM=xcb
python3 desktop_app/main.py
```

### Voice button does nothing

**Fix**:
```bash
# Check microphone
arecord -l

# Reinstall audio
sudo apt-get install --reinstall portaudio19-dev
pip install --force-reinstall PyAudio
```

### "CLAUDE_API_KEY not found"

**Fix**:
```bash
# Make sure .env exists
ls -la .env

# Add key
echo "CLAUDE_API_KEY=sk-ant-your-key" > .env
```

## \ud83d\udcda Documentation

- **Full docs**: `README.md`
- **Installation**: `INSTALL.md`
- **Deployment**: `DEPLOYMENT.md`
- **Structure**: `PROJECT_STRUCTURE.md`

## \u2705 Testing

Verify installation:

```bash
python3 test_onyx.py
```

Should show:
```
🎉 All tests passed! ONYX is ready to run.
```

## \ud83d\udcbc Packaging for Others

Create distributable package:

```bash
chmod +x package_onyx.sh
./package_onyx.sh
```

Output: `/tmp/onyx-1.0.0-linux.tar.gz`

Share this file with others. They just extract and run!

## \ud83c\udfae Demo Flow

1. **Start ONYX**
   ```bash
   python3 desktop_app/main.py
   ```

2. **Create chat**
   - Click "+ New Chat"

3. **Text message**
   - Type: "Tell me a short joke"
   - Press Send
   - See response

4. **Voice message** (requires working microphone)
   - Click \ud83c\udfa4 button
   - Say: "What is Python?"
   - See transcription
   - Send message

5. **Manage chats**
   - Create another chat
   - Switch between chats
   - Rename a chat
   - Delete a chat

6. **Customize personality**
   - Edit `Onyx/config/personality.txt`
   - Restart ONYX
   - Try new conversation style

## \ud83d\udca1 Pro Tips

1. **Keyboard focus**: Message input has focus after each response
2. **Multiline input**: Text input supports multiple lines
3. **Conversation context**: Each chat maintains its own context
4. **Local data**: Everything stored in `Onyx/` folder
5. **Logs available**: Check `Onyx/logs/` for troubleshooting
6. **Backup chats**: Copy `Onyx/history/chats.db`
7. **Personality templates**: Keep multiple personality files

## \ud83d\udd17 Useful Links

- **Claude Console**: https://console.anthropic.com/
- **Claude Pricing**: https://anthropic.com/pricing
- **Whisper Models**: https://github.com/openai/whisper#available-models-and-languages
- **PySide6 Docs**: https://doc.qt.io/qtforpython/

## \ud83c\udd98 Support

If stuck:

1. Run tests: `python3 test_onyx.py`
2. Check logs: `cat Onyx/logs/onyx_*.log`
3. Read troubleshooting: See `README.md` or `INSTALL.md`
4. Verify dependencies: `pip list | grep -E 'PySide|whisper|torch'`

## \u2764\ufe0f Enjoy!

ONYX is your local, private AI assistant.
No cloud. No tracking. Your data stays with you.

Happy chatting! \ud83e\udd16
