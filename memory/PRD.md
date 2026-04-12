# ONYX — Persistent Desktop AI (Letta-first)

## Architecture
```
  User -> PySide6 UI -> ChatService (thin relay) -> LettaBridge -> Letta Server -> Anthropic
                                 |                       |
                          SQLite (mirror)         Supabase (app state)
```

- **Letta** = brain. Owns persona, human memory, identity, context compaction, tools, model calls
- **Anthropic** = model provider configured on Letta server. NOT called directly by UI
- **Supabase** = app state mirror (tasks, events, files). NOT a second brain
- **SQLite** = UI display mirror. NOT used for cognition
- **UI** = interface only. Sends ONLY the user's message text to Letta

## What was removed (Letta owns these)
- `context_service.py` — local transcript summarization for model context. DELETED.
- `personality_service.py` — local persona/kb/instructions wrapper. DELETED.
- `tool_service.py` — local shell/file tools + prompt injection. DELETED.
- `storage_service.py` brain logic — DEFAULT_PERSONALITY, DEFAULT_KNOWLEDGEBASE, DEFAULT_USER_PROFILE, DEFAULT_INSTRUCTIONS, build_system_message(), get_personality(), get_knowledgebase(), get_user_profile(), get_instructions(), summaries table. ALL STRIPPED.
- Direct Anthropic SDK calls from chat path. REMOVED.

## Normal message turn (after cleanup)
```
1. User types message
2. ChatService.send_message(text, chat_id)
3. Mirror user msg to SQLite (for UI display)
4. bridge.send_message(text=message) — sends ONLY the text
5. Letta handles: persona, human memory, context window, compaction, tools, model call
6. Bridge returns {response, tool_calls, usage}
7. Mirror assistant response to SQLite (for UI display)
8. UI renders response
```

## Env vars
```
LETTA_BASE_URL=http://localhost:8283   # REQUIRED
LETTA_API_KEY=                          # Optional for self-hosted
LETTA_AGENT_ID=                         # Optional, auto-creates
ANTHROPIC_API_KEY=                      # Set on Letta server, not used by UI
SUPABASE_URL=                           # Optional
SUPABASE_ANON_KEY=                      # Optional
```

## Files
```
desktop_app/
  main.py                    # Entry: config validation, health check, wiring
  services/
    letta_bridge.py          # Real letta-client SDK: connect, agent CRUD, send_message, memory
    chat_service.py          # Thin relay: UI -> bridge -> SQLite mirror
    storage_service.py       # SQLite mirror (chats/messages) + app settings. No brain logic.
    supabase_service.py      # Cloud state: tasks, events, files, agent state
    voice_service.py         # Whisper STT
    tts_service.py           # Piper TTS
  ui/
    main_window.py           # 3-panel: sidebar | chat | inspector
    chat_widget.py           # Chat display, lazy loading, voice
    inspector_panel.py       # Letta state, memory blocks, tasks, events, files
    avatar_widget.py         # Animated robot
    styles.py                # Dark theme
```

## 13/13 tests passing
Tests verify: no direct Anthropic, no brain in storage, dead files removed, clean Letta bridge, env vars correct.
