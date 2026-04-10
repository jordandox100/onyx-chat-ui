# ONYX — Local Desktop AI Chat Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with:
- PySide6 dark modern UI (sleek, cyber-tech aesthetic)
- Local SQLite database for chat history with context continuity
- Local folder structure (Onyx/history, config, voice, logs)
- Claude Sonnet 4.6 default (switchable to any Anthropic model)
- Local Whisper for speech-to-text + wake word "Onyx"
- Text-to-Speech with UI toggle
- Tool use: shell commands, file read/write, directory listing
- Streaming responses (typed out word-by-word)
- File attachments
- System tray + compact mode toggle

## Architecture
```
/app/
├── desktop_app/
│   ├── main.py                    # Entry point
│   ├── ui/
│   │   ├── main_window.py         # Main window + sidebar + tray + compact toggle
│   │   ├── chat_widget.py         # Chat + streaming + model dropdown + attachments
│   │   └── styles.py              # Dark theme + HTML message templates
│   └── services/
│       ├── storage_service.py     # SQLite CRUD + config file management
│       ├── chat_service.py        # Claude via emergentintegrations + history + tools
│       ├── tool_service.py        # Shell/file/dir tools for ONYX
│       ├── voice_service.py       # Whisper STT + wake word thread
│       ├── tts_service.py         # pyttsx3 TTS with settings persistence
│       └── personality_service.py
├── Onyx/config/
│   ├── personality.txt            # Agent personality
│   ├── knowledgebase.txt          # Persistent facts
│   ├── user.txt                   # User profile
│   ├── instructions.txt           # Custom rules
│   └── settings.json              # App settings (model, TTS, etc.)
├── install/
│   ├── setup.sh                   # Venv-based installer
│   ├── onyx_icon.svg              # Futuristic robot icon
│   └── onyx_icon.png
├── requirements.txt
└── .env                           # CLAUDE_API_KEY= (user fills in)
```

## What's Implemented (Feb 2026)
- [x] PySide6 dark UI with cyber-tech color scheme (electric cyan accent)
- [x] SQLite storage with full CRUD
- [x] Chat history context — old chats resume with full context injection
- [x] Model dropdown: 9 Anthropic models (Sonnet 4.6 default)
- [x] Streaming responses (word-by-word typing effect via QTimer)
- [x] Tool use: shell commands, file read/write, directory listing
- [x] File attachments via file picker (text content inlined)
- [x] System tray icon with minimize-to-tray on close
- [x] Compact mode toggle (arrow hides/shows sidebar)
- [x] Text-to-Speech via pyttsx3 with UI toggle + settings persistence
- [x] Voice-to-text via local Whisper (push-to-talk)
- [x] Wake word "Onyx" background listener via Whisper
- [x] Configuration system: personality, knowledgebase, user profile, instructions, settings
- [x] Futuristic humanoid robot SVG/PNG icon
- [x] Venv-based install script with proper emergentintegrations install
- [x] Distinct user (blue) vs agent (cyan border) message styling
- [x] Tool output display (green border, monospace)
- [x] 119 pytest tests + 9 integration tests, 100% pass rate

## Key Dependencies
- PySide6 >= 6.8.0
- emergentintegrations (--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/)
- pyttsx3 (espeak-ng on Linux)
- openai-whisper, torch, pyaudio

## Configuration
- `.env`: Set `CLAUDE_API_KEY=sk-ant-...`
- `Onyx/config/personality.txt`: Agent personality
- `Onyx/config/knowledgebase.txt`: Facts ONYX should always know
- `Onyx/config/user.txt`: User profile
- `Onyx/config/instructions.txt`: Custom rules
- `Onyx/config/settings.json`: App settings

## Backlog
- P2: TTS voice selection UI
- P2: Conversation export/import
- P3: Drag-and-drop file attachments
