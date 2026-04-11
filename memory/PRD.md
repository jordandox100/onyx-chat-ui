# ONYX — Local Desktop AI Chat Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with modern dark UI, local persistence, Claude AI (direct Anthropic SDK), local Whisper STT, neural TTS with British/Jarvis voices, tool execution, and a one-command installer.

## Architecture
```
/app/
├── install_onyx.sh                    # ONE-CLICK INSTALLER
├── desktop_app/
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py             # Sidebar, tray, compact mode
│   │   ├── chat_widget.py             # Chat, code blocks, avatar, voice controls, stop button
│   │   ├── avatar_widget.py           # Animated robot head (moves mouth when speaking)
│   │   └── styles.py                  # Dark cyber-tech theme + code block template
│   └── services/
│       ├── storage_service.py         # SQLite CRUD + config
│       ├── chat_service.py            # Anthropic SDK, 13 models with descriptions, cancel support
│       ├── tool_service.py            # Shell/file/dir tools
│       ├── voice_service.py           # Whisper STT + wake word
│       └── tts_service.py             # Piper neural TTS — speed, naturalness, stop/restart/preview
├── Onyx/
│   ├── config/ (personality, knowledgebase, user, instructions, settings)
│   ├── history/chats.db
│   ├── voices/ (5 neural TTS models)
│   └── logs/
├── requirements.txt
├── test_onyx.py (13 test suites)
└── .env (CLAUDE_API_KEY=)
```

## What's Implemented (Feb 2026)
- [x] PySide6 dark cyber-tech UI
- [x] Direct Anthropic SDK (no emergentintegrations)
- [x] 13 Anthropic models with descriptions in dropdown
- [x] Animated robot avatar — head bobs, mouth moves while TTS speaks
- [x] Code blocks rendered in styled boxes with Copy button, excluded from TTS
- [x] Stop agent button — cancels LLM response mid-flight
- [x] Neural TTS with 5 voices: Jarvis (British RP), Northern British, Spike, Obadiah, Ryan
- [x] Voice preview button — hear voice before selecting
- [x] Speed slider (0.5x — 2.0x) for TTS
- [x] Enhanced naturalness (noise_scale=0.8, noise_w_scale=0.9)
- [x] TTS stop/restart buttons
- [x] Streaming responses (code blocks appear instantly, text streams)
- [x] SQLite chat history with context continuity
- [x] Tool use: shell, file read/write, directory listing
- [x] File attachments, system tray, compact mode
- [x] Enter to send / Shift+Enter for newline
- [x] Wake word "Onyx" background listener
- [x] One-command installer (install_onyx.sh)
- [x] 13/13 test suites passing

## TTS Voices
| Voice | Model | Description |
|---|---|---|
| Jarvis (British RP) | en_GB-alan-medium | Refined British male (JARVIS style) |
| British Male — Northern | en_GB-northern_english_male-medium | Northern English accent |
| British Male — Spike | en_GB-semaine-medium (speaker 1) | British male |
| British Male — Obadiah | en_GB-semaine-medium (speaker 2) | British male |
| American Male — Ryan | en_US-ryan-medium | American male |

## Backlog
- P2: Conversation export/import
- P3: Drag-and-drop file attachments
- P3: Additional voice models (female voices, accents)
