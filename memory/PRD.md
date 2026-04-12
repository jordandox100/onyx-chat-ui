# ONYX — Supabase + Anthropic Runtime, Conditional Tools

## Architecture
```
User -> UI -> ChatService -> OnyxRuntime -> [Router] -> Anthropic API
                  |               |                        |
             SQLite (mirror)  Supabase         tools (only when needed)
```

## Normal Turn (no tools — default, cheapest)
```
Input:
  system: persona + summary + goals + beliefs + memories (~800 tokens)
  messages: last 6 only (~3000 tokens)
  tools: NONE
  Total: ~4000 tokens

Output:
  direct text response
```

## Tool Turn (only when request requires it)
```
1. Router classifies request (heuristic, zero-cost)
2. Selects minimal bundle:
   - direct_answer -> no tools (default)
   - web_lookup    -> [web_search] (1 tool)
   - memory_lookup -> [memory_search] (1 tool)
   - file_lookup   -> [file_read, file_search] (2 tools)
   - code_work     -> [file_read, file_write, shell_exec] (3 tools)
   - multi_tool    -> minimal combination (4 tools max)
3. Anthropic call includes only selected tools
4. Tool calls executed, results fed back (max 3 rounds)
```

## Env Vars
```
ANTHROPIC_API_KEY=    # REQUIRED
SUPABASE_URL=         # Persistent memory
SUPABASE_ANON_KEY=    # Persistent memory
```

## Files
```
desktop_app/services/
  runtime.py          # OnyxRuntime: router + direct/tool execution paths
  tool_router.py      # Heuristic classifier + minimal bundles
  tool_executor.py    # Real tool implementations (shell, file, memory, web)
  chat_service.py     # Thin relay: UI -> runtime -> SQLite mirror
  storage_service.py  # Local SQLite (display mirror + settings)
  supabase_service.py # Cloud: conversations, messages, memories, beliefs, goals, tasks, events, files
  voice_service.py    # Whisper STT
  tts_service.py      # Piper TTS
desktop_app/ui/
  main_window.py      # 3-panel: sidebar | chat | inspector
  chat_widget.py      # Chat display, lazy loading, voice
  inspector_panel.py  # Agent state, summary, goals, beliefs, tasks, events, files, memories
  avatar_widget.py    # Animated robot
  styles.py           # Dark theme
```

## What Was Removed
- letta_bridge.py — DELETED
- letta-client — removed from requirements
- LETTA_* env vars — removed
- All always-on tool attachment — NONE by default
- Transcript replay — max 6 messages

## 11/11 Tests Passing
