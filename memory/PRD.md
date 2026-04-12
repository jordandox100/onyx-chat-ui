# ONYX — Supabase + Anthropic, Auth, Safety Filter, Shared Folders

## Architecture
```
Login -> PySide6 UI -> ChatService -> [Safety Filter] -> [Router] -> Anthropic
              |                                              |
         SQLite (mirror)                              Supabase (state)
```

## Auth
- Supabase `users` table with bcrypt-hashed passwords
- Admin: onyxadmin / Gem266726!
- Admin can: view all users, access all data, delete anything, bypass safety filter
- Regular users: private data, blocked key phrases

## Safety Filter Pipeline
1. Normalize (lowercase, unicode, leetspeak, collapse whitespace)
2. Exact phrase blocklist (130+ phrases)
3. N-gram/substring scan (danger terms)
4. Fuzzy similarity (SequenceMatcher, 85% threshold)
5. Spaced evasion detection (g h o s t g u n)
Admin bypasses all filters.

## Shared Folders
- Create by entering another user's username
- Both users can read/add items
- Only the adder can delete their own items
- Admin can delete anything

## Config Files (Onyx/config/)
- personality.txt, knowledgebase.txt, user.txt, instructions.txt
- Feed into runtime system prompt
- Admin-editable

## Env Vars
```
ANTHROPIC_API_KEY=    # REQUIRED
SUPABASE_URL=         # Auth + persistent state
SUPABASE_ANON_KEY=    # Auth + persistent state
```

## Files
```
desktop_app/services/
  runtime.py, chat_service.py, storage_service.py, supabase_service.py
  auth_service.py, safety_filter.py, shared_service.py
  tool_router.py, tool_executor.py
  voice_service.py, tts_service.py
desktop_app/ui/
  main_window.py, chat_widget.py, inspector_panel.py
  login_dialog.py, avatar_widget.py, styles.py
```

## 11/11 Tests Passing
