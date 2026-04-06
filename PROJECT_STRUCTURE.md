# ONYX Application

## Project Structure

```
/app/
├── desktop_app/              # Main application code
│   ├── main.py              # Entry point
│   ├── ui/                  # User interface
│   │   ├── main_window.py   # Main window
│   │   ├── chat_widget.py   # Chat interface
│   │   └── styles.py        # Dark theme
│   ├── services/            # Business logic
│   │   ├── chat_service.py          # AI integration
│   │   ├── voice_service.py         # Voice I/O
│   │   ├── storage_service.py       # Data persistence
│   │   └── personality_service.py   # Config management
│   ├── models/              # Data models
│   └── utils/               # Utilities
│       └── logger.py        # Logging
│
├── Onyx/                    # User data directory
│   ├── history/             # Chat database
│   ├── config/              # Configuration
│   ├── voice/               # Voice data
│   └── logs/                # Application logs
│
├── requirements.txt         # Python dependencies
├── .env                     # API keys
├── README.md                # Documentation
├── INSTALL.md               # Installation guide
├── DEPLOYMENT.md            # Deployment guide
├── run_onyx.sh              # Launcher script
├── test_onyx.py             # Test suite
└── package_onyx.sh          # Packaging script
```

## Key Files

### Configuration
- `.env` - API keys and environment variables
- `Onyx/config/personality.txt` - AI personality
- `requirements.txt` - Python package dependencies

### Application
- `desktop_app/main.py` - Application entry point
- `desktop_app/ui/main_window.py` - Main window and layout
- `desktop_app/ui/chat_widget.py` - Chat interface
- `desktop_app/services/chat_service.py` - Claude AI integration
- `desktop_app/services/voice_service.py` - Whisper voice input
- `desktop_app/services/storage_service.py` - SQLite database

### Data
- `Onyx/history/chats.db` - SQLite database
- `Onyx/config/personality.txt` - AI personality
- `Onyx/logs/onyx_*.log` - Application logs

### Documentation
- `README.md` - Full documentation
- `INSTALL.md` - Installation instructions
- `DEPLOYMENT.md` - Deployment guide
- `START_HERE.txt` - Quick start (in package)

## Development

### Adding Features

1. **New UI Component**:
   - Add to `desktop_app/ui/`
   - Import in `main_window.py`
   - Update styles in `styles.py`

2. **New Service**:
   - Create in `desktop_app/services/`
   - Initialize in relevant UI component
   - Add tests to `test_onyx.py`

3. **New Model/Data Structure**:
   - Add to `desktop_app/models/`
   - Update `storage_service.py` for persistence
   - Migrate database if needed

### Modifying AI Behavior

Edit `desktop_app/services/chat_service.py`:
```python
# Change model
self.llm_chat.with_model("anthropic", "claude-sonnet-4-6")

# Modify system prompt
self.personality = "Your custom personality here"
```

### Modifying Voice Settings

Edit `desktop_app/services/voice_service.py`:
```python
# Change Whisper model
self.whisper_model = whisper.load_model("small")  # tiny, base, small, medium, large

# Change recording duration
self.RECORD_SECONDS = 10  # seconds
```

### Modifying UI Theme

Edit `desktop_app/ui/styles.py`:
```python
# Change colors
"background-color: #4a9eff;"  # Primary (blue)
"background-color: #0a0a0a;"  # Dark background
"color: #e0e0e0;"              # Text color
```

## Testing

Run test suite:
```bash
python3 test_onyx.py
```

Test individual components:
```bash
# Storage
python3 -c "from desktop_app.services.storage_service import StorageService; s=StorageService(); s.initialize(); print('OK')"

# Chat (requires API key)
python3 -c "import asyncio; from desktop_app.services.chat_service import ChatService; asyncio.run(ChatService().send_message('Hi', 1))"

# Voice
python3 -c "from desktop_app.services.voice_service import VoiceService; v=VoiceService(); print('OK' if v.whisper_model else 'No model')"
```

## Building

Create distributable package:
```bash
chmod +x package_onyx.sh
./package_onyx.sh
```

Output: `/tmp/onyx-1.0.0-linux.tar.gz`

## Database Schema

### chats table
```sql
CREATE TABLE chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### messages table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);
```

## Dependencies

### Python Packages
- **PySide6**: Qt GUI framework
- **emergentintegrations**: AI integration library
- **openai-whisper**: Speech-to-text
- **torch/torchaudio**: Whisper dependencies
- **PyAudio**: Audio recording
- **python-dotenv**: Environment variables
- **aiohttp**: Async HTTP
- **numpy**: Numerical operations

### System Libraries
- **Qt5**: GUI library
- **PortAudio**: Audio I/O
- **ALSA**: Linux audio

## Environment Variables

- `CLAUDE_API_KEY`: Anthropic API key (required)
- `ONYX_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `QT_QPA_PLATFORM`: Qt platform (xcb, wayland)
- `DISPLAY`: X11 display

## Logs

Logs are written to:
- `Onyx/logs/onyx_YYYYMMDD.log`
- Console output

Log levels:
- DEBUG: Detailed debugging information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages

Set log level:
```bash
export ONYX_LOG_LEVEL=DEBUG
python3 desktop_app/main.py
```

## Performance

### Resource Usage
- **RAM**: 200MB base + 500MB per Whisper model
- **CPU**: Minimal idle, high during transcription
- **Disk**: ~100KB per chat, ~150MB for Whisper model
- **Network**: Only for AI API calls

### Optimization Tips
1. Use smaller Whisper model ("tiny" or "base")
2. Limit conversation history
3. Close unused chats
4. Regular database vacuum
5. Use Claude Sonnet instead of Opus

## Security

- API keys stored in `.env` (not in code)
- Local data not encrypted
- No network access except AI API
- No telemetry or tracking
- All data stays local

## Known Limitations

1. Linux only (not Mac/Windows)
2. Requires display server
3. Single user
4. No cloud sync
5. Wake word requires additional setup
6. No mobile version
7. English optimized (voice)

## Future Enhancements

- [ ] Complete wake word detection
- [ ] Text-to-speech responses
- [ ] Multi-language support
- [ ] Cloud sync option
- [ ] Mobile companion app
- [ ] Plugin system
- [ ] Code syntax highlighting
- [ ] File attachments
- [ ] Export conversations
- [ ] Keyboard shortcuts

## License

MIT License - See LICENSE file

## Support

For issues:
1. Check logs in `Onyx/logs/`
2. Run `python3 test_onyx.py`
3. See INSTALL.md troubleshooting
4. Read DEPLOYMENT.md for environment issues
