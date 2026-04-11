"""Context service — replaces raw history replay with summaries + recent window.

Old approach: send last 20 messages every turn (~10K tokens).
New approach: compact summary + last 6 messages (~3.5K tokens). ~65% reduction.
"""
from typing import List, Dict, Tuple, Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()

RECENT_WINDOW = 6       # Only send last N messages as raw API context
SUMMARY_INTERVAL = 8    # Regenerate summary every N new messages
MAX_SUMMARY_MSGS = 20   # Summarize at most this many recent older messages


class ContextService:
    """Manages conversation context efficiently to minimize token usage."""

    def __init__(self, storage, supabase=None):
        self.storage = storage
        self.supabase = supabase
        self._summaries: Dict[int, str] = {}
        self._summary_counts: Dict[int, int] = {}

    def build_context(self, chat_id: int, new_message: str,
                      system_message: str) -> Tuple[str, list]:
        """Build optimized (system_message, messages) for Anthropic API.

        Returns:
            enhanced_system: system message with conversation summary appended
            messages: list of recent messages + new user message
        """
        all_msgs = self.storage.get_chat_messages(chat_id)
        total = len(all_msgs)

        enhanced = system_message

        if total > RECENT_WINDOW:
            summary = self._ensure_summary(chat_id, all_msgs)
            if summary:
                enhanced += (
                    "\n\n--- Prior Conversation Context ---\n"
                    "The following is a compact summary of the earlier part of this conversation. "
                    "Use it for continuity but do not repeat or reference it directly.\n"
                    f"{summary}"
                )

        recent = all_msgs[-RECENT_WINDOW:] if total > RECENT_WINDOW else all_msgs
        messages = [{"role": m["role"], "content": m["content"]} for m in recent]
        messages.append({"role": "user", "content": new_message})

        logger.info(
            f"Context built: {total} total msgs, {len(recent)} recent, "
            f"summary={'yes' if total > RECENT_WINDOW else 'no'}"
        )
        return enhanced, messages

    def maybe_update_summary(self, chat_id: int):
        """Regenerate summary if enough new messages since last generation."""
        total = self.storage.get_message_count(chat_id)
        last_count = self._summary_counts.get(chat_id, 0)

        if total - last_count >= SUMMARY_INTERVAL:
            all_msgs = self.storage.get_chat_messages(chat_id)
            self._generate_and_save(chat_id, all_msgs, total)

    def get_conversation_summary(self, chat_id: int) -> str:
        """Return cached or stored summary for a conversation."""
        if chat_id in self._summaries:
            return self._summaries[chat_id]

        stored = self.storage.get_summary(chat_id)
        if stored:
            self._summaries[chat_id] = stored
            return stored
        return ""

    def force_refresh_summary(self, chat_id: int) -> str:
        """Force regeneration of conversation summary."""
        all_msgs = self.storage.get_chat_messages(chat_id)
        total = len(all_msgs)
        if total > RECENT_WINDOW:
            self._generate_and_save(chat_id, all_msgs, total)
        return self._summaries.get(chat_id, "")

    def clear_summary(self, chat_id: int):
        self._summaries.pop(chat_id, None)
        self._summary_counts.pop(chat_id, None)

    # ── Internal ──────────────────────────────────────────────

    def _ensure_summary(self, chat_id: int, all_msgs: list) -> str:
        """Return existing summary or generate one."""
        if chat_id in self._summaries:
            return self._summaries[chat_id]

        stored = self.storage.get_summary(chat_id)
        if stored:
            self._summaries[chat_id] = stored
            return stored

        total = len(all_msgs)
        if total > RECENT_WINDOW:
            return self._generate_and_save(chat_id, all_msgs, total)
        return ""

    def _generate_and_save(self, chat_id: int, all_msgs: list,
                           total: int) -> str:
        older = all_msgs[:-RECENT_WINDOW] if len(all_msgs) > RECENT_WINDOW else []
        summary = self._generate_summary_text(older)
        self._summaries[chat_id] = summary
        self._summary_counts[chat_id] = total
        self.storage.save_summary(chat_id, summary, total)
        logger.info(f"Summary updated for chat {chat_id} ({total} msgs)")
        return summary

    @staticmethod
    def _generate_summary_text(messages: list) -> str:
        """Generate compact text summary. Bounded to ~500 tokens max."""
        if not messages:
            return ""

        count = len(messages)
        if count > 40:
            subset = messages[:5] + messages[-MAX_SUMMARY_MSGS:]
            prefix = f"Conversation so far ({count} exchanges). Key points:\n"
        else:
            subset = messages[-MAX_SUMMARY_MSGS:]
            prefix = f"Prior conversation ({count} exchanges):\n"

        lines = []
        for m in subset:
            role = "User" if m["role"] == "user" else "ONYX"
            text = m["content"][:150].replace("\n", " ").strip()
            if len(m["content"]) > 150:
                text += "..."
            lines.append(f"- {role}: {text}")

        return prefix + "\n".join(lines)
