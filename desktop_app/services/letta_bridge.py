"""Letta backend bridge — clean interfaces for persistent agent operations.

In local mode (no remote Letta server), delegates to:
  - ContextService + direct Anthropic calls for chat
  - Supabase for extended state (tasks, events, files, agent state)
  - SQLite for local chat history

Ready for real Letta backend hookup by implementing these methods against
a Letta server instead of local services.
"""
from pathlib import Path
from typing import Optional, List, Dict

from desktop_app.utils.logger import get_logger

logger = get_logger()


class LettaBridge:
    """Bridge between UI and Letta agent runtime."""

    def __init__(self, supabase=None, context_service=None, chat_service=None):
        self.supabase = supabase
        self.context = context_service
        self.chat = chat_service
        self._agent_id = "onyx"

    # ── Chat ──────────────────────────────────────────────────

    async def send_message_to_agent(self, conversation_id: int, user_id: str,
                                    text: str, on_tool_output=None,
                                    cancel_flag=None) -> str:
        """Send a message through the agent runtime."""
        if not self.chat:
            return "[Bridge error] No chat service configured."
        return await self.chat.send_message(
            text, conversation_id,
            on_tool_output=on_tool_output,
            cancel_flag=cancel_flag,
        )

    # ── Agent State ───────────────────────────────────────────

    def get_agent_state(self, agent_id: str = None) -> dict:
        agent_id = agent_id or self._agent_id
        state = {
            "agent_id": agent_id,
            "status": "active",
            "model": "",
            "heartbeat": None,
            "active_conversation": None,
            "working_summary": "",
            "goals": [],
            "preferences": {},
        }
        if self.chat:
            state["model"] = self.chat.model_name
        if self.supabase and self.supabase.available:
            remote = self.supabase.get_agent_state(agent_id)
            if remote:
                state.update({k: v for k, v in remote.items() if v is not None})
        return state

    def update_agent_state(self, **fields) -> bool:
        if self.supabase and self.supabase.available:
            return self.supabase.upsert_agent_state(self._agent_id, **fields)
        return False

    # ── Summaries ─────────────────────────────────────────────

    def get_conversation_summary(self, conversation_id: int) -> str:
        if self.context:
            return self.context.get_conversation_summary(conversation_id)
        return ""

    def get_memory_summary(self, conversation_id: int = None) -> dict:
        state = self.get_agent_state()
        summary = ""
        if conversation_id and self.context:
            summary = self.context.get_conversation_summary(conversation_id)
        return {
            "conversation_summary": summary,
            "working_memory": state.get("working_summary", ""),
            "goals": state.get("goals", []),
            "preferences": state.get("preferences", {}),
        }

    # ── Tasks ─────────────────────────────────────────────────

    def get_tasks(self, user_id: str = "local") -> List[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.get_tasks(user_id)
        return []

    def create_task(self, title: str, conv_id: str = None) -> Optional[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.create_task(title, conv_id)
        return None

    def retry_task(self, task_id: str) -> bool:
        if self.supabase and self.supabase.available:
            return self.supabase.update_task(task_id, status="active")
        return False

    # ── Events ────────────────────────────────────────────────

    def get_events(self, user_id: str = "local", limit: int = 50) -> List[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.get_events(user_id, limit)
        return []

    def log_event(self, event_type: str, content: str,
                  conv_id: str = None) -> Optional[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.log_event(event_type, content, conv_id)
        return None

    # ── Files ─────────────────────────────────────────────────

    def get_files(self, user_id: str = "local",
                  conversation_id: str = None) -> List[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.get_files(user_id, conversation_id)
        return []

    def process_uploaded_file(self, file_path: str,
                              conversation_id: int = None,
                              user_id: str = "local") -> dict:
        p = Path(file_path)
        meta = {
            "name": p.name,
            "path": str(p),
            "size": p.stat().st_size if p.exists() else 0,
            "content_type": "",
        }
        if self.supabase and self.supabase.available:
            result = self.supabase.register_file(
                meta["name"], meta["path"], meta["size"],
                conv_id=str(conversation_id) if conversation_id else None,
                user_id=user_id,
            )
            if result:
                meta["id"] = result.get("id")
        return meta

    # ── Messages (lazy loading) ───────────────────────────────

    def load_recent_messages(self, conversation_id: int, limit: int = 20) -> List[Dict]:
        """Load recent messages for display (NOT for prompt context)."""
        if self.chat and self.chat.storage:
            msgs = self.chat.storage.get_chat_messages(conversation_id)
            return msgs[-limit:]
        return []

    def load_messages_page(self, conversation_id: int,
                           offset: int = 0, limit: int = 20) -> List[Dict]:
        """Load a page of older messages for display."""
        if self.chat and self.chat.storage:
            return self.chat.storage.get_messages_page(
                conversation_id, offset, limit
            )
        return []

    def get_message_count(self, conversation_id: int) -> int:
        if self.chat and self.chat.storage:
            return self.chat.storage.get_message_count(conversation_id)
        return 0
