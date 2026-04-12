# ONYX — Letta Server Setup Guide

## Quick Start (Docker)

### 1. Start Letta Server

```bash
docker run -d \
  --name letta-server \
  -p 8283:8283 \
  -v ~/.letta/.persist/pgdata:/root/.persist/pgdata \
  -e LETTA_ANTHROPIC_API_KEY=your_anthropic_api_key_here \
  lettaai/letta:latest
```

**Replace** `your_anthropic_api_key_here` with your actual Anthropic API key.

### 2. Verify Server

```bash
# Check it's running
docker logs letta-server

# Health check
curl http://localhost:8283/health
```

### 3. Configure ONYX

Edit your `.env` file:

```
LETTA_BASE_URL=http://localhost:8283
LETTA_API_KEY=
LETTA_AGENT_ID=
ANTHROPIC_API_KEY=your_anthropic_api_key
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

- `LETTA_BASE_URL` — **Required.** Your Letta server URL.
- `LETTA_API_KEY` — Optional for self-hosted. Required for Letta Cloud.
- `LETTA_AGENT_ID` — Optional. ONYX auto-creates an agent if not set.
- `ANTHROPIC_API_KEY` — Your Anthropic key (also set on the Letta server via `LETTA_ANTHROPIC_API_KEY`).
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` — Optional. For cloud state sync (tasks, events, files).

### 4. Start ONYX

```bash
cd /app && python desktop_app/main.py
```

ONYX will:
1. Connect to Letta server
2. Run a health check
3. Find or create the ONYX agent (with persona + human memory blocks)
4. Show "LETTA READY" in the inspector panel

## What Letta Handles

| Feature | Letta | Local |
|---------|-------|-------|
| Chat memory | Persistent across sessions | Mirror in SQLite for UI display |
| Identity (persona) | Memory block | — |
| User profile (human) | Memory block | — |
| Context compaction | Automatic | — |
| Tool execution | Letta built-in tools | — |
| Model selection | `anthropic/claude-*` | — |

## Supabase Setup (Optional)

For task tracking, event logging, and file management, run `supabase_setup.sql` in your Supabase SQL Editor, then add credentials to `.env`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "LETTA NOT SET" in inspector | Set `LETTA_BASE_URL` in `.env` |
| "Connection failed" | Check Docker is running: `docker ps` |
| Agent creation fails | Ensure `LETTA_ANTHROPIC_API_KEY` is set on the Docker container |
| Slow responses | Try a faster model: Haiku 4.5 or Sonnet 4.6 |
