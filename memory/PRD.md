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
- Streaming responses, file attachments, system tray, compact mode
- One-command installer: `./install_onyx.sh`

## Installation
```bash
git clone https://github.com/jordandox100/onyx-chat-ui.git
cd onyx-chat-ui
./install_onyx.sh
```
That's it. The script handles everything: system deps, Python venv, packages, TTS voice models, asks for your API key, and launches the app.

## Architecture
```
/app/
├── install_onyx.sh                # ONE-CLICK INSTALLER (run this)
├── launch_onyx.sh                 # Generated launcher
├── desktop_app/
│   ├── main.py                    # Entry point
│   ├── ui/
│   │   ├── main_window.py         # Main window + sidebar + tray
│   │   ├── chat_widget.py         # Chat + streaming + model/voice dropdowns
│   │   └── styles.py              # Dark cyber-tech theme
│   └── services/
│       ├── storage_service.py     # SQLite CRUD + config management
│       ├── chat_service.py        # Claude via anthropic SDK directly
│       ├── tool_service.py        # Shell/file/dir tools
│       ├── voice_service.py       # Whisper STT + wake word
│       └── tts_service.py         # Piper neural TTS (5 voices)
├── Onyx/
│   ├── config/ (personality, knowledgebase, user, instructions, settings)
│   ├── history/chats.db
│   ├── voices/ (5 neural TTS models, ~330MB)
│   └── logs/
├── requirements.txt
├── test_onyx.py (11 test suites)
└── .env (CLAUDE_API_KEY=)
```

## What's Implemented (Feb 2026)
- [x] PySide6 dark UI with cyber-tech color scheme
- [x] Direct Anthropic SDK (NO emergentintegrations)
- [x] 13 Anthropic models in dropdown (Sonnet 4.6 default)
- [x] SQLite chat history with context continuity
- [x] Streaming responses (word-by-word typing effect)
- [x] Tool use: shell, file read/write, directory listing
- [x] File attachments via file picker
- [x] System tray + compact mode toggle
- [x] Neural TTS: Jarvis (British RP), Northern British, Spike, Obadiah, American Ryan
- [x] Voice-to-text via local Whisper (push-to-talk)
- [x] Wake word "Onyx" background listener
- [x] Config files: personality, knowledgebase, user profile, instructions
- [x] Enter to send / Shift+Enter for newline
- [x] Auto-rename new chats from first message
- [x] One-command installer (`./install_onyx.sh`)
- [x] Desktop shortcut with futuristic robot icon
- [x] 11 test suites, all passing

## TTS Voices
| Voice | Model | Description |
|---|---|---|
| Jarvis (British RP) | en_GB-alan-medium | Refined British male (Iron Man style) |
| British Male — Northern | en_GB-northern_english_male-medium | Northern English accent |
| British Male — Spike | en_GB-semaine-medium (speaker 1) | British male |
| British Male — Obadiah | en_GB-semaine-medium (speaker 2) | British male |
| American Male — Ryan | en_US-ryan-medium | American male |

## Backlog
- P2: Conversation export/import
- P3: Drag-and-drop file attachments
- P3: Additional voice models (female, Scottish, etc.)
