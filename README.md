# ONYX - Local Linux Desktop AI Assistant

![ONYX](https://img.shields.io/badge/ONYX-AI%20Assistant-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![PySide6](https://img.shields.io/badge/GUI-PySide6-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What is ONYX?

ONYX is a **local Linux desktop AI chat assistant** with a modern, polished interface. It features:

- ✨ **Modern Dark UI** - Sleek, ChatGPT-style interface
- 💾 **Local Storage** - All chats and settings stored locally
- 🧠 **AI-Powered** - Uses Claude Opus 4.6 for intelligent responses
- 🎤 **Voice Input** - Push-to-talk with local Whisper transcription
- 📝 **Personality Customization** - Edit the AI's personality
- 📚 **Chat History** - Persistent chat management
- 🚀 **Fast & Responsive** - No lag, smooth scrolling

## Features

### Core Functionality

1. **Chat Interface**
   - Conversation list in sidebar
   - Clean message bubbles
   - Smooth scrolling
   - No page refresh issues
   - Stable rendering

2. **Chat Management**
   - Create new chats
   - Rename chats
   - Delete chats
   - Load chat history
   - Automatic persistence

3. **Voice Input**
   - Push-to-talk recording (5 seconds)
   - Local Whisper speech-to-text
   - Wake word support ("Onyx") - framework ready
   - Visual recording indicator

4. **Local Storage Structure**
```
Onyx/
├── history/
│   └── chats.db          # SQLite database
├── config/
│   └── personality.txt   # AI personality configuration
├── voice/                # Voice recordings and models
└── logs/                 # Application logs
```

5. **Personality System**
   - Customizable AI personality
   - Stored in `Onyx/config/personality.txt`
   - Applied to every conversation
   - Easy to edit

## Installation

### System Requirements

- **OS**: Linux (Debian/Ubuntu tested)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum (8GB recommended for Whisper)
- **Disk**: 2GB free space

### Linux Setup

#### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    qtbase5-dev \
    qt5-qmake \
    libqt5widgets5 \
    portaudio19-dev \
    python3-pyaudio
```

#### 2. Install Python Dependencies

```bash
cd /app
pip install -r requirements.txt
```

**Requirements:**
- PySide6 (Qt GUI framework)
- anthropic (AI integration)
- python-dotenv (Environment variables)
- openai-whisper (Local speech-to-text)
- torch, torchaudio (Whisper dependencies)
- PyAudio (Audio recording)
- numpy (Numerical operations)

#### 3. Configure API Key

Edit the `.env` file and add your Claude API key:

```bash
CLAUDE_API_KEY=your_api_key_here
```

**Get your API key:**
- Go to [https://console.anthropic.com/](https://console.anthropic.com/)
- Create an account or sign in
- Generate an API key
- Copy and paste it into `.env`

#### 4. Run ONYX

```bash
# Method 1: Direct Python
python3 desktop_app/main.py

# Method 2: Using launcher script
chmod +x run_onyx.sh
./run_onyx.sh
```

## Usage Guide

### Starting ONYX

1. Run the application:
   ```bash
   python3 desktop_app/main.py
   ```

2. The ONYX window will open with:
   - Left sidebar for chat management
   - Main chat area in the center

### Creating Chats

1. Click **"+ New Chat"** button in sidebar
2. Type your message and press **Send** or hit Enter
3. Chat will be automatically saved and named

### Managing Chats

- **Switch chats**: Click on any chat in the sidebar
- **Rename chat**: Select chat and click **Rename** button
- **Delete chat**: Select chat and click **Delete** button

### Using Voice Input

1. Click the **🎤 microphone button**
2. Speak clearly for up to 5 seconds
3. Button turns red (⏺) while recording
4. Transcription appears in message input
5. Edit if needed, then send

**Note**: First time using Whisper will download the model (~150MB)

### Customizing Personality

1. Navigate to `Onyx/config/personality.txt`
2. Edit the text file with your preferred personality
3. Restart ONYX to apply changes
4. All future conversations will use the new personality

**Example personality:**
```text
You are ONYX, a helpful and intelligent AI assistant.

Your personality:
- Professional yet friendly
- Clear and concise
- Patient and understanding
- Knowledgeable across many topics
- Always honest
- Respectful
```

## Architecture

### Technology Stack

- **GUI Framework**: PySide6 (Qt for Python)
- **AI Model**: Claude Opus 4.6 via anthropic
- **Database**: SQLite3
- **Voice-to-Text**: OpenAI Whisper (local)
- **Audio**: PyAudio + PortAudio

### Project Structure

```
/app/
├── desktop_app/
│   ├── main.py                 # Entry point
│   ├── ui/
│   │   ├── main_window.py       # Main application window
│   │   ├── chat_widget.py       # Chat display and input
│   │   └── styles.py            # Dark theme styles
│   ├── services/
│   │   ├── chat_service.py      # AI chat logic
│   │   ├── voice_service.py     # Voice recording/transcription
│   │   ├── storage_service.py   # Database operations
│   │   └── personality_service.py
│   └── utils/
│       └── logger.py            # Logging utility
├── Onyx/                      # Local data directory
├── .env                       # API keys
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Service Layer

- **StorageService**: Manages SQLite database, file storage
- **ChatService**: Handles AI communication via Claude
- **VoiceService**: Records audio and transcribes with Whisper
- **PersonalityService**: Loads and applies personality configuration

## Troubleshooting

### Common Issues

#### 1. "CLAUDE_API_KEY not found"

**Solution**: Edit `.env` file and add your API key:
```bash
CLAUDE_API_KEY=sk-ant-your-key-here
```

#### 2. Voice button doesn't work

**Solutions**:
- Check microphone permissions
- Verify PortAudio is installed:
  ```bash
  sudo apt-get install portaudio19-dev
  ```
- Check logs in `Onyx/logs/`

#### 3. Whisper model download fails

**Solutions**:
- Check internet connection
- Verify disk space (need ~500MB)
- Manually download:
  ```python
  import whisper
  whisper.load_model("base")
  ```

#### 4. Qt/PySide6 issues

**Solutions**:
- Install Qt system libraries:
  ```bash
  sudo apt-get install qtbase5-dev qt5-qmake
  ```
- Reinstall PySide6:
  ```bash
  pip uninstall PySide6
  pip install PySide6
  ```

#### 5. Application won't start

**Debug steps**:
1. Check logs: `cat Onyx/logs/onyx_*.log`
2. Run with verbose output:
   ```bash
   python3 desktop_app/main.py 2>&1 | tee debug.log
   ```
3. Verify all dependencies:
   ```bash
   pip list | grep -E 'PySide6|emergent|whisper|torch'
   ```

### Performance Tips

1. **Whisper Model Selection**:
   - `tiny`: Fastest, least accurate (~39MB)
   - `base`: Balanced (default, ~150MB)
   - `small`: Better accuracy (~500MB)
   - `medium`: High accuracy (~1.5GB)
   - `large`: Best quality (~3GB)

   Change in `voice_service.py`:
   ```python
   self.whisper_model = whisper.load_model("tiny")  # or base, small, etc.
   ```

2. **Database Optimization**:
   - Periodically vacuum: `sqlite3 Onyx/history/chats.db "VACUUM;"`

3. **Memory Usage**:
   - Close unused chats
   - Restart app if it slows down

## Wake Word Detection

The wake word "Onyx" is **framework-ready** but requires additional setup:

### Implementation Options

1. **Porcupine** (Recommended):
   - Custom wake word training
   - Requires Picovoice account
   - Low latency

2. **Snowboy** (Archived):
   - Open source
   - No longer maintained

3. **Custom Model**:
   - Train with your own data
   - Use TensorFlow/PyTorch

### Current Status

The `VoiceService` has placeholder methods:
- `start_wake_word_detection()`
- `stop_wake_word_detection()`

These can be implemented with your preferred wake word engine.

## Customization

### Changing the Theme

Edit `desktop_app/ui/styles.py` to modify colors:

```python
# Primary color (blue accent)
"background-color: #4a9eff;"

# Dark backgrounds
"background-color: #0a0a0a;"  # Main
"background-color: #111111;"  # Sidebar
"background-color: #1a1a1a;"  # Input
```

### Changing Voice Recording Duration

Edit `desktop_app/services/voice_service.py`:

```python
self.RECORD_SECONDS = 10  # Change from 5 to 10 seconds
```

### Changing AI Model

Edit `desktop_app/services/chat_service.py`:

```python
# Current: Claude Opus 4.6
self.llm_chat.with_model("anthropic", "claude-opus-4-6")

# Change to Claude Sonnet:
self.llm_chat.with_model("anthropic", "claude-sonnet-4-6")

# Or another provider:
self.llm_chat.with_model("openai", "gpt-5.2")
```

## Development

### Running in Development Mode

```bash
# Enable debug logging
export ONYX_LOG_LEVEL=DEBUG
python3 desktop_app/main.py
```

### Building for Distribution

Create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile \
    --windowed \
    --name ONYX \
    --icon icon.ico \
    desktop_app/main.py

# Output in dist/ONYX
```

### Testing

Run basic functionality tests:

```bash
python3 -m pytest tests/
```

## API Key and Costs

### Claude API Pricing

Claude Opus 4.6:
- Input: ~$15 per 1M tokens
- Output: ~$75 per 1M tokens

**Typical conversation**:
- 10 messages = ~5,000 tokens
- Cost: ~$0.02-0.05 per conversation

### Managing Costs

1. **Use a cheaper model** (Sonnet instead of Opus)
2. **Shorter personality prompts**
3. **Limit conversation history** (modify `chat_service.py`)
4. **Monitor usage** at https://console.anthropic.com/

## Roadmap

### Planned Features

- [ ] Full wake word detection
- [ ] Text-to-speech responses
- [ ] Multi-language support
- [ ] Cloud sync (optional)
- [ ] Plugin system
- [ ] Code syntax highlighting
- [ ] File attachment support
- [ ] Export conversations
- [ ] Dark/Light theme toggle
- [ ] Keyboard shortcuts

### Known Limitations

1. **No display server**: Won't run in headless environments
2. **Linux only**: Not tested on Mac/Windows
3. **Wake word**: Requires additional setup
4. **Single user**: No multi-user support
5. **No encryption**: Local data not encrypted

## Contributing

Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file

## Credits

- **AI**: Anthropic Claude Opus 4.6
- **Speech**: OpenAI Whisper
- **GUI**: Qt Project (PySide6)
- **Integration**: anthropic library

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `Onyx/logs/`
3. Open an issue with:
   - Error message
   - Log file excerpt
   - Steps to reproduce

## Acknowledgments

Built with care for the Linux desktop community.

---

**ONYX** - Your local AI assistant, your way.
