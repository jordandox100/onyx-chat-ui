# ONYX — Persistent Desktop AI Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with persistent agent architecture using Letta as the full runtime (chat, memory, identity, continuity, compaction), Supabase for app-visible state, and PySide6 for the desktop UI.

## Architecture
```
                    ┌─────────────────────┐
                    │    PySide6 UI        │
                    │  (product interface) │
                    └──────┬──────────────┘
                           │
                    ┌──────▼──────────────┐
                    │   Letta Bridge       │
                    │  (backend connector) │
                    └──┬──────────────┬───┘
                       │              │
              ┌────────▼────┐  ┌──────▼──────┐
              │ Letta Server │  │  Supabase   │
              │ (agent mind) │  │ (app state) │
              └──────────────┘  └─────────────┘
                    │
              ┌─────▼─────┐
              │ Anthropic  │
              │ (LLM model)│
              └────────────┘

/app/
├── LETTA_SETUP.md                     # Server setup guide
├── supabase_setup.sql                 # Supabase schema
├── install_onyx.sh                    # ONE-CLICK INSTALLER
├── desktop_app/
│   ├── main.py                        # Entry — config validation, Letta health, wiring
│   ├── ui/
│   │   ├── main_window.py             # 3-panel: sidebar | chat | inspector
│   │   ├── chat_widget.py             # Chat display, lazy loading, voice
│   │   ├── inspector_panel.py         # Agent state, Letta memory blocks, tasks, events
│   │   ├── avatar_widget.py           # Animated robot head
│   │   └── styles.py                  # Dark cyber-tech theme
│   └── services/
│       ├── letta_bridge.py            # REAL Letta client — agent CRUD, messaging, memory
│       ├── chat_service.py            # Routes through Letta (no direct Anthropic)
│       ├── supabase_service.py        # Cloud state (tasks, events, files)
│       ├── storage_service.py         # Local SQLite (UI mirror + summaries)
│       ├── context_service.py         # Smart context for fallback/summary generation
│       ├── tool_service.py            # Shell/file tools
│       ├── voice_service.py           # Whisper STT
│       └── tts_service.py             # Piper neural TTS
├── Onyx/ (config, history, voices, logs)
├── requirements.txt
├── test_onyx.py (16 test suites)
└── .env
```

## Runtime Architecture
- **Letta** = primary runtime. Handles chat, memory, identity, context compaction
- **Anthropic** = model provider configured ON the Letta server (not called directly)
- **Supabase** = app-visible state (tasks, events, files, agent state mirror)
- **SQLite** = local UI display mirror only (not used for cognition)
- **No transcript replay** = Letta handles its own memory/compaction internally

## Env Vars
```
LETTA_BASE_URL=http://localhost:8283   # Required — Letta server URL
LETTA_API_KEY=                          # Optional for self-hosted
LETTA_AGENT_ID=                         # Optional — auto-creates ONYX agent
ANTHROPIC_API_KEY=                      # For reference / other uses
SUPABASE_URL=                           # Optional — cloud state sync
SUPABASE_ANON_KEY=                      # Optional
```

## What's Implemented (Feb 2026)

### Letta Integration
- [x] Real letta-client SDK integration (letta_bridge.py)
- [x] Agent creation with persona + human memory blocks
- [x] Message routing through Letta (persistent memory, compaction)
- [x] Agent state retrieval from Letta server
- [x] Memory block reading (persona, human blocks)
- [x] Conversation message history from Letta
- [x] Streaming message support (send_message_streaming)
- [x] Health checks and config validation at startup
- [x] Clean "not configured" state when Letta is missing
- [x] Logging of which runtime path is used per message turn

### Desktop UI
- [x] PySide6 dark cyber-tech UI
- [x] 3-panel layout: sidebar | chat | inspector (both toggleable)
- [x] Inspector panel showing Letta agent state, memory blocks, tasks, events, files
- [x] Lazy message loading with "Load older messages" button
- [x] Animated robot avatar
- [x] Code blocks with copy buttons (excluded from TTS)
- [x] Neural TTS (5 Piper voices), voice preview, speed slider
- [x] Stop agent button, TTS stop/restart
- [x] Wake word "Onyx"

### Token Waste Eliminated
- Direct Anthropic calls with 20-message replay REMOVED
- Letta handles context compaction internally
- Local SQLite is display-only, not cognition source
- Context service available as fallback summary generator

## Backlog
- P0: Test end-to-end with live Letta server + Anthropic key
- P1: Supabase table creation + live state sync testing
- P2: Conversation export/import
- P3: Additional voice models
- P3: Realtime Supabase subscriptions
