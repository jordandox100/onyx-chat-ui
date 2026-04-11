# ONYX — Persistent Desktop AI Assistant

## Problem Statement
Build a local Linux desktop AI chat assistant called ONYX with modern dark UI, persistent agent architecture (Letta-backed memory + Supabase state), local Whisper STT, neural TTS, tool execution, and efficient token management that replaces raw history replay with summaries.

## Architecture
```
/app/
├── install_onyx.sh                    # ONE-CLICK INSTALLER
├── supabase_setup.sql                 # Supabase schema setup
├── desktop_app/
│   ├── main.py                        # Entry point — wires services + bridge
│   ├── ui/
│   │   ├── main_window.py             # Sidebar, chat, inspector panel, tray
│   │   ├── chat_widget.py             # Chat, code blocks, avatar, voice, lazy loading
│   │   ├── inspector_panel.py         # Right panel: agent state, tasks, events, files, memory
│   │   ├── avatar_widget.py           # Animated robot head
│   │   └── styles.py                  # Dark cyber-tech theme + all templates
│   └── services/
│       ├── storage_service.py         # SQLite CRUD + summaries + pagination
│       ├── supabase_service.py        # Supabase cloud state (optional, graceful fallback)
│       ├── context_service.py         # Smart context: summary + recent window (replaces 20-msg replay)
│       ├── letta_bridge.py            # Backend bridge: UI <-> Letta/Supabase/chat
│       ├── chat_service.py            # Anthropic SDK, context-aware, cancel support
│       ├── tool_service.py            # Shell/file/dir tools
│       ├── voice_service.py           # Whisper STT + wake word
│       └── tts_service.py             # Piper neural TTS
├── Onyx/
│   ├── config/ (personality, knowledgebase, user, instructions, settings)
│   ├── history/chats.db
│   ├── voices/ (5 neural TTS models)
│   └── logs/
├── requirements.txt
├── test_onyx.py (16 test suites)
└── .env (CLAUDE_API_KEY=, SUPABASE_URL=, SUPABASE_ANON_KEY=)
```

## What's Implemented (Feb 2026)

### Core Desktop App
- [x] PySide6 dark cyber-tech UI
- [x] Direct Anthropic SDK (no emergentintegrations)
- [x] 13 Anthropic models with descriptions in dropdown
- [x] Animated robot avatar — head bobs, mouth moves while TTS speaks
- [x] Code blocks rendered in styled boxes with Copy button, excluded from TTS
- [x] Stop agent button — cancels LLM response mid-flight
- [x] Neural TTS with 5 voices including Jarvis
- [x] Voice preview, speed slider (0.5x-2.0x), stop/restart
- [x] Streaming responses with code block support
- [x] SQLite chat history with context continuity
- [x] Tool use: shell, file read/write, directory listing
- [x] File attachments, system tray, compact mode
- [x] Wake word "Onyx" background listener
- [x] One-command installer (install_onyx.sh)

### Persistent Architecture (NEW)
- [x] Context Service — replaces 20-message history replay with summary + last 6 messages (~65% token reduction)
- [x] Supabase Service — cloud state layer for conversations, messages, tasks, events, files, agent state (optional, graceful fallback)
- [x] Letta Bridge — clean interfaces connecting UI to persistent agent runtime
- [x] Inspector Panel — right-side panel showing agent state, conversation summary, tasks, events, files, memory
- [x] Lazy message loading — "Load older messages" button, only displays recent 20 on load
- [x] Summary generation — auto-generates conversation summaries stored in SQLite summaries table
- [x] Pagination — get_messages_page, get_message_count for efficient history access
- [x] 3-panel layout — sidebar | chat | inspector with toggle buttons
- [x] Polling refresh — inspector auto-refreshes every 15 seconds
- [x] Supabase SQL schema provided (supabase_setup.sql)
- [x] 16/16 test suites passing

## Token Waste Removed
| Pattern | Before | After |
|---|---|---|
| Messages per API call | Last 20 raw messages (~10K tokens) | Summary + last 6 (~3.5K tokens) |
| History loading | ALL messages loaded eagerly | Paginated, lazy display |
| Context building | UI constructs giant prompt payload | Context service manages compactly |
| Summary usage | None | Auto-generated, cached in SQLite |

## Env Vars Required
- `CLAUDE_API_KEY` — Anthropic API key (required for chat)
- `SUPABASE_URL` — Supabase project URL (optional)
- `SUPABASE_ANON_KEY` — Supabase anon key (optional)

## Backlog
- P1: Supabase table creation + real data flow testing with live credentials
- P2: Conversation export/import
- P2: LLM-powered summarization (use Haiku to create better summaries)
- P3: Drag-and-drop file attachments
- P3: Additional voice models (female voices)
- P3: Real Letta server integration (replace local bridge with remote)
- P3: Realtime Supabase subscriptions for live sync
