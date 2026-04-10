# ONYX — Local Desktop AI Chat Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with:
- PySide6 dark modern UI (sleek, cyber-tech aesthetic)
- Local SQLite database for chat history with context continuity
- Local folder structure (Onyx/history, config, voice, logs, voices)
- Claude Sonnet 4.6 default (dropdown of ALL 13 Anthropic models)
- Direct Anthropic SDK — user provides their own API key in .env
- Local Whisper for speech-to-text + wake word "Onyx"
- Neural Text-to-Speech via Piper with 5 voice options (incl. Jarvis British RP)
- Tool use: shell commands, file read/write, directory listing
- Streaming responses (typed out word-by-word)
- File attachments
- System tray + compact mode toggle
- Enter to send, Shift+Enter for newline

## Architecture
```
/app/
├── desktop_app/
│   ├── main.py                    # Entry point
│   ├── ui/
│   │   ├── main_window.py         # Main window + sidebar + tray + compact toggle
│   │   ├── chat_widget.py         # Chat + streaming + model dropdown + voice selector
│   │   └── styles.py              # Dark theme + HTML message templates
│   └── services/
│       ├── storage_service.py     # SQLite CRUD + config file management
│       ├── chat_service.py        # Claude via anthropic SDK + history + tools
│       ├── tool_service.py        # Shell/file/dir tools for ONYX
│       ├── voice_service.py       # Whisper STT + wake word thread
│       ├── tts_service.py         # Piper neural TTS with voice selection
│       └── personality_service.py
├── Onyx/
│   ├── config/
│   │   ├── personality.txt        # Agent personality
│   │   ├── knowledgebase.txt      # Persistent facts
│   │   ├── user.txt               # User profile
│   │   ├── instructions.txt       # Custom rules
│   │   └── settings.json          # App settings (model, TTS, voice, etc.)
│   ├── history/chats.db
│   ├── logs/
│   ├── voice/
│   └── voices/                    # Piper neural TTS models (~330MB)
│       ├── en_GB-alan-medium.onnx       # Jarvis (British RP)
│       ├── en_GB-northern_english_male-medium.onnx
│       ├── en_GB-semaine-medium.onnx    # Multi-speaker (Spike, Obadiah)
│       ├── en_GB-aru-medium.onnx
│       └── en_US-ryan-medium.onnx       # American male
├── install/
│   ├── setup.sh                   # Venv-based installer + voice download
│   ├── onyx_icon.svg
│   └── onyx_icon.png
├── requirements.txt               # anthropic, piper-tts, PySide6, etc.
├── test_onyx.py                   # 11 test suites
└── .env                           # CLAUDE_API_KEY= (user fills in)
```

## What's Implemented (Feb 2026)
- [x] PySide6 dark UI with cyber-tech color scheme (electric cyan accent)
- [x] SQLite storage with full CRUD
- [x] Chat history context — old chats resume with full message history
- [x] Model dropdown: 13 Anthropic models (Sonnet 4.6 default)
- [x] Direct Anthropic SDK (no emergentintegrations)
- [x] Streaming responses (word-by-word typing effect via QTimer)
- [x] Tool use: shell commands, file read/write, directory listing
- [x] File attachments via file picker (text content inlined)
- [x] System tray icon with minimize-to-tray on close
- [x] Compact mode toggle (arrow hides/shows sidebar)
- [x] Neural TTS via Piper with 5 voice options + UI dropdown
- [x] Jarvis (British RP), British Northern, British Spike, British Obadiah, American Ryan
- [x] Voice-to-text via local Whisper (push-to-talk)
- [x] Wake word "Onyx" background listener via Whisper
- [x] Configuration: personality, knowledgebase, user profile, instructions, settings
- [x] Enter to send / Shift+Enter for newline
- [x] Auto-rename new chats from first message
- [x] Model dropdown doesn't fire on startup (loading guard)
- [x] Futuristic humanoid robot SVG/PNG icon
- [x] Venv-based install script with voice model download
- [x] Distinct user (blue) vs agent (cyan border) message styling
- [x] Tool output display (green border, monospace)
- [x] 11 test suites, all passing

## Key Dependencies
- PySide6 >= 6.8.0
- anthropic >= 0.90.0
- piper-tts >= 1.4.0
- openai-whisper, torch, pyaudio (optional for voice)

## Configuration
- `.env`: Set `CLAUDE_API_KEY=sk-ant-...`
- `Onyx/config/personality.txt`: Agent personality
- `Onyx/config/knowledgebase.txt`: Facts ONYX should always know
- `Onyx/config/user.txt`: User profile
- `Onyx/config/instructions.txt`: Custom rules
- `Onyx/config/settings.json`: App settings

## TTS Voices
| Voice Name | Model | Type |
|---|---|---|
| Jarvis (British RP) | en_GB-alan-medium | Refined British male |
| British Male — Northern | en_GB-northern_english_male-medium | Northern English male |
| British Male — Spike | en_GB-semaine-medium (speaker 1) | British male |
| British Male — Obadiah | en_GB-semaine-medium (speaker 2) | British male |
| American Male — Ryan | en_US-ryan-medium | American male |

## Backlog
- P2: Conversation export/import
- P3: Drag-and-drop file attachments
- P3: Additional voice models (female voices, accents)
