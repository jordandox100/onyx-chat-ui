# ONYX — Local Desktop AI Chat Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with:
- PySide6 dark modern UI (ChatGPT-like)
- Local SQLite database for chat history
- Local folder structure (Onyx/history, config, voice, logs)
- Claude Opus 4.6 for AI responses (via emergentintegrations)
- Local Whisper for speech-to-text
- Text-to-Speech for AI responses (toggleable in UI)
- One-click install script using venv

## Architecture
```
/app/
├── desktop_app/
│   ├── main.py                  # Entry point
│   ├── ui/
│   │   ├── main_window.py       # Main window + sidebar
│   │   ├── chat_widget.py       # Chat area + TTS toggle
│   │   └── styles.py            # Dark theme QSS
│   └── services/
│       ├── storage_service.py   # SQLite CRUD
│       ├── chat_service.py      # Claude Opus 4.6 via emergentintegrations
│       ├── voice_service.py     # Whisper STT (push-to-talk)
│       ├── tts_service.py       # pyttsx3 text-to-speech
│       └── personality_service.py
├── Onyx/                        # Local data
│   ├── config/personality.txt
│   ├── history/chats.db
│   ├── logs/
│   └── voice/
├── install/
│   └── setup.sh                 # Venv-based installer
├── requirements.txt
└── .env                         # CLAUDE_API_KEY= (user fills in)
```

## What's Implemented (Feb 2026)
- [x] PySide6 dark modern UI with sidebar chat management
- [x] SQLite storage (chats + messages CRUD)
- [x] Claude Opus 4.6 integration (emergentintegrations library)
- [x] Local Whisper speech-to-text (push-to-talk button)
- [x] Text-to-Speech via pyttsx3 with UI toggle ("Voice Replies" checkbox)
- [x] Local personality configuration file
- [x] venv-based install script (setup.sh) with proper emergentintegrations install
- [x] Desktop shortcut + launcher script
- [x] Comprehensive test suite (51 pytest + 7 integration tests, 100% pass)

## Key Dependencies
- PySide6 >= 6.8.0
- emergentintegrations (via --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/)
- pyttsx3 (uses espeak-ng on Linux)
- openai-whisper, torch, pyaudio

## Configuration
- `.env`: Set `CLAUDE_API_KEY=sk-ant-...` to enable AI chat
- `Onyx/config/personality.txt`: Edit to customise ONYX's personality

## Backlog
- P1: Wake word "Onyx" — continuous background listening via Whisper (needs careful threading to avoid UI freeze)
- P2: TTS voice selection in UI settings
- P2: Conversation export/import
