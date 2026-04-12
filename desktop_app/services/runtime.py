"""ONYX Runtime — Supabase-backed agent with direct Anthropic calls.

No Letta. No transcript replay. No hidden overhead.

Per-turn cost:
  System prompt (~800 tokens): persona + state summary + goals + beliefs + memories
  Recent messages (last 6, ~3000 tokens)
  User message (~200 tokens)
  Total: ~4000 tokens input per turn

After each turn:
  - Store message pair in Supabase
  - Periodically update conversation summary
  - Extract and store new memories
"""
import os
from typing import Optional, List, Dict
from datetime import datetime, timezone

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

PERSONA = (
    "You are ONYX, a persistent AI assistant on the user's Linux desktop. "
    "You are sharp, direct, technically savvy, and genuinely helpful. "
    "You have persistent memory across sessions — you remember past conversations. "
    "Be concise. Solve the real problem. Adapt tone to the user."
)

RECENT_WINDOW = 6        # Messages sent as raw context
SUMMARY_INTERVAL = 8     # Update summary every N messages
DEFAULT_MODEL = "claude-sonnet-4-6"


class OnyxRuntime:
    """Custom agent runtime: Supabase state + direct Anthropic calls.

    No Letta dependency. Compact prompt. Persistent memory.
    """

    def __init__(self, supabase=None):
        self.supabase = supabase
        self._client = None
        self._model = DEFAULT_MODEL
        self._configured = False
        self._connect()

    def _connect(self):
        if not ANTHROPIC_AVAILABLE:
            logger.warning("anthropic SDK not installed")
            return
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            logger.warning("ANTHROPIC_API_KEY not set")
            return
        self._client = anthropic.Anthropic(api_key=key)
        self._configured = True
        logger.info("Anthropic client ready")

    @property
    def available(self) -> bool:
        return self._configured and self._client is not None

    @property
    def status(self) -> str:
        if not ANTHROPIC_AVAILABLE:
            return "SDK_MISSING"
        if not self._configured:
            return "NOT_CONFIGURED"
        return "READY"

    @property
    def status_detail(self) -> str:
        if not ANTHROPIC_AVAILABLE:
            return "pip install anthropic"
        if not self._configured:
            return "Set ANTHROPIC_API_KEY in .env"
        return f"Ready — model: {self._model}"

    @property
    def model(self) -> str:
        return self._model

    def set_model(self, model: str):
        self._model = model

    # ── Chat ──────────────────────────────────────────────────

    def send_message(self, text: str, conversation_id: int,
                     user_id: str = "local",
                     local_messages: list = None) -> dict:
        """Send message with compact context. Returns response dict.

        Prompt structure (cheap):
          system = persona + conversation_summary + goals + beliefs + memories
          messages = last 6 messages + new user message
        """
        if not self.available:
            return {"response": f"[Runtime not ready: {self.status_detail}]",
                    "usage": {}}

        # Build compact system prompt from Supabase state
        system = self._build_system_prompt(conversation_id, user_id)

        # Build message list: recent window + new message
        messages = self._build_messages(conversation_id, text, local_messages)

        logger.info(
            f"[runtime] model={self._model}, system={len(system)} chars, "
            f"msgs={len(messages)}"
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            reply = response.content[0].text if response.content else ""
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
            logger.info(
                f"[runtime] response={len(reply)} chars, tokens={usage}"
            )

            # Store in Supabase
            self._persist_turn(conversation_id, user_id, text, reply)

            # Periodic summary update
            self._maybe_update_summary(conversation_id, user_id)

            return {"response": reply, "usage": usage}

        except Exception as e:
            logger.error(f"[runtime] Anthropic error: {e}")
            return {"response": f"[Error: {e}]", "usage": {}}

    # ── Prompt Building (compact) ─────────────────────────────

    def _build_system_prompt(self, conversation_id: int,
                             user_id: str) -> str:
        """Build small system prompt from Supabase state."""
        parts = [PERSONA]

        if not self.supabase or not self.supabase.available:
            return parts[0]

        # Conversation summary
        summary = self._get_summary(conversation_id)
        if summary:
            parts.append(f"\n=== Conversation So Far ===\n{summary}")

        # Active goals
        goals = self._get_goals(user_id)
        if goals:
            goal_text = "\n".join(
                f"- [{g.get('status','?')}] {g.get('title','')}"
                for g in goals[:5]
            )
            parts.append(f"\n=== Active Goals ===\n{goal_text}")

        # Key beliefs
        beliefs = self._get_beliefs(user_id)
        if beliefs:
            belief_text = "\n".join(
                f"- {b.get('content','')}"
                for b in beliefs[:8]
            )
            parts.append(f"\n=== What I Know About You ===\n{belief_text}")

        # Relevant memories
        memories = self._get_memories(user_id, conversation_id)
        if memories:
            mem_text = "\n".join(
                f"- {m.get('content','')}"
                for m in memories[:6]
            )
            parts.append(f"\n=== Relevant Memories ===\n{mem_text}")

        return "\n".join(parts)

    def _build_messages(self, conversation_id: int, new_text: str,
                        local_messages: list = None) -> list:
        """Recent message window + new user message. No full transcript."""
        messages = []

        # Try Supabase first, fall back to local SQLite messages
        if self.supabase and self.supabase.available:
            recent = self.supabase.get_recent_messages(
                str(conversation_id), limit=RECENT_WINDOW
            )
            for m in recent:
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", ""),
                })
        elif local_messages:
            for m in local_messages[-RECENT_WINDOW:]:
                messages.append({
                    "role": m.get("role", "user"),
                    "content": m.get("content", ""),
                })

        messages.append({"role": "user", "content": new_text})
        return messages

    # ── Supabase State Reads ──────────────────────────────────

    def _get_summary(self, conversation_id: int) -> str:
        if not self.supabase or not self.supabase.available:
            return ""
        try:
            conv = self.supabase.get_conversation(str(conversation_id))
            return (conv or {}).get("summary", "") or ""
        except Exception:
            return ""

    def _get_goals(self, user_id: str) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_goals(user_id)
        except Exception:
            return []

    def _get_beliefs(self, user_id: str) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_beliefs(user_id)
        except Exception:
            return []

    def _get_memories(self, user_id: str, conversation_id: int) -> list:
        if not self.supabase or not self.supabase.available:
            return []
        try:
            return self.supabase.get_memories(user_id, limit=6)
        except Exception:
            return []

    # ── Supabase State Writes ─────────────────────────────────

    def _persist_turn(self, conversation_id: int, user_id: str,
                      user_text: str, assistant_text: str):
        """Mirror the turn to Supabase."""
        if not self.supabase or not self.supabase.available:
            return
        cid = str(conversation_id)
        self.supabase.add_message(cid, "user", user_text)
        self.supabase.add_message(cid, "assistant", assistant_text)

    def _maybe_update_summary(self, conversation_id: int, user_id: str):
        """Periodically regenerate conversation summary (every N turns)."""
        if not self.supabase or not self.supabase.available:
            return
        if not self._client:
            return

        cid = str(conversation_id)
        count = self.supabase.get_message_count(cid)
        if count < SUMMARY_INTERVAL:
            return

        # Check if summary is stale
        conv = self.supabase.get_conversation(cid)
        if not conv:
            return
        existing = conv.get("summary", "") or ""
        # Simple heuristic: update if summary is short relative to message count
        if len(existing) > 50 and count < (SUMMARY_INTERVAL * 2):
            return

        recent = self.supabase.get_recent_messages(cid, limit=20)
        if not recent:
            return

        # Use cheapest model for summary generation
        transcript = "\n".join(
            f"{m.get('role','?')}: {m.get('content','')[:200]}"
            for m in recent
        )
        try:
            resp = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                system="Summarize this conversation in 2-3 sentences. Be factual and concise.",
                messages=[{"role": "user", "content": transcript}],
            )
            summary = resp.content[0].text if resp.content else ""
            if summary:
                self.supabase.update_conversation(cid, summary=summary)
                logger.info(f"Summary updated for conv {cid}")
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")

    # ── State Accessors (for inspector panel) ─────────────────

    def get_agent_state(self) -> dict:
        return {
            "status": self.status,
            "status_detail": self.status_detail,
            "model": self._model,
            "runtime": "supabase+anthropic",
            "name": "ONYX",
        }

    def get_conversation_summary(self, conversation_id: int) -> str:
        return self._get_summary(conversation_id)

    def get_goals(self, user_id: str = "local") -> list:
        return self._get_goals(user_id)

    def get_beliefs(self, user_id: str = "local") -> list:
        return self._get_beliefs(user_id)

    def get_memories(self, user_id: str = "local", limit: int = 10) -> list:
        return self._get_memories(user_id, 0)

    def get_tasks(self, user_id: str = "local") -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_tasks(user_id)
        return []

    def get_events(self, user_id: str = "local", limit: int = 50) -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_events(user_id, limit)
        return []

    def get_files(self, user_id: str = "local",
                  conversation_id: str = None) -> list:
        if self.supabase and self.supabase.available:
            return self.supabase.get_files(user_id, conversation_id)
        return []
