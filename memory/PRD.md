# ONYX — Supabase + Anthropic Runtime (No Letta)

## Architecture
```
User -> PySide6 UI -> ChatService -> OnyxRuntime -> Anthropic API
                          |               |
                     SQLite (mirror)  Supabase (persistent state)
```

- **OnyxRuntime** = direct Anthropic calls with compact Supabase-backed context
- **Supabase** = persistent store: conversations, messages, memories, beliefs, goals, tasks, events, files
- **SQLite** = local UI display mirror only
- **No Letta** — removed entirely (too expensive, too heavy)

## Per-Turn Cost
```
System (~800 tok): persona + summary + goals + beliefs + memories
Messages (~3000 tok): last 6 messages only
User input (~200 tok)
Total: ~4000 tokens/turn (vs Letta's hidden overhead)
```

## Env Vars
```
ANTHROPIC_API_KEY=    # REQUIRED
SUPABASE_URL=         # Persistent memory
SUPABASE_ANON_KEY=    # Persistent memory
```

## Files
```
desktop_app/
  main.py                    # Entry — config validation, wiring
  services/
    runtime.py               # OnyxRuntime: Anthropic calls + Supabase state + compact prompt
    chat_service.py           # Thin relay: UI -> runtime -> SQLite mirror
    storage_service.py        # Local SQLite (display mirror + settings)
    supabase_service.py       # Cloud: conversations, messages, memories, beliefs, goals, tasks, events, files
    voice_service.py          # Whisper STT
    tts_service.py            # Piper TTS
  ui/
    main_window.py            # 3-panel: sidebar | chat | inspector
    chat_widget.py            # Chat display, lazy loading, voice controls
    inspector_panel.py        # Agent state, summary, goals, beliefs, tasks, events, files, memories
    avatar_widget.py          # Animated robot
    styles.py                 # Dark theme
```

## What Was Removed
- `letta_bridge.py` — DELETED (464 lines)
- `letta-client` — removed from requirements.txt
- `LETTA_BASE_URL`, `LETTA_API_KEY`, `LETTA_AGENT_ID` — removed from .env
- All Letta SDK imports, client code, agent management, memory block reads — gone
- Inspector panel rewired from Letta bridge to runtime + supabase directly

## Inspector Panels
Agent State | Conversation Summary | Goals | Beliefs | Tasks | Events | Files | Memories
All backed by Supabase (or empty state when unconfigured).

## 10/10 Tests Passing
