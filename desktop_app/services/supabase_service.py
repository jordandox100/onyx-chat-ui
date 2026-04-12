"""Supabase service — persistent cloud state layer for ONYX.
Gracefully falls back when not configured."""
import os
from typing import Optional, List, Dict
from datetime import datetime, timezone

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class SupabaseService:
    """Persistent state backed by Supabase. All methods return safe defaults when unconfigured."""

    def __init__(self):
        self._client: Optional[Client] = None
        self._configured = False
        self._connect()

    def _connect(self):
        if not SUPABASE_AVAILABLE:
            logger.info("supabase-py not installed. Cloud sync disabled.")
            return
        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
        if not url or not key:
            logger.info("SUPABASE_URL/SUPABASE_ANON_KEY not set. Cloud sync disabled.")
            return
        try:
            self._client = create_client(url, key)
            self._configured = True
            logger.info("Supabase connected.")
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")

    @property
    def available(self) -> bool:
        return self._configured and self._client is not None

    @property
    def status_text(self) -> str:
        if not SUPABASE_AVAILABLE:
            return "NOT INSTALLED"
        if not self._configured:
            return "NOT CONFIGURED"
        return "CONNECTED"

    # ── Conversations ─────────────────────────────────────────

    def create_conversation(self, title: str, user_id: str = "local",
                            agent_id: str = "onyx") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = self._client.table("conversations").insert({
                "title": title, "user_id": user_id, "agent_id": agent_id,
                "summary": "", "archived": False,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase create_conversation: {e}")
            return None

    def get_conversations(self, user_id: str = "local",
                          include_archived: bool = False) -> List[Dict]:
        if not self.available:
            return []
        try:
            q = self._client.table("conversations").select("*").eq("user_id", user_id)
            if not include_archived:
                q = q.eq("archived", False)
            result = q.order("updated_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_conversations: {e}")
            return []

    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = (self._client.table("conversations")
                      .select("*").eq("id", conv_id).single().execute())
            return result.data
        except Exception as e:
            logger.error(f"supabase get_conversation: {e}")
            return None

    def update_conversation(self, conv_id: str, **fields) -> bool:
        if not self.available:
            return False
        try:
            fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._client.table("conversations").update(fields).eq("id", conv_id).execute()
            return True
        except Exception as e:
            logger.error(f"supabase update_conversation: {e}")
            return False

    def archive_conversation(self, conv_id: str) -> bool:
        return self.update_conversation(conv_id, archived=True)

    # ── Messages ──────────────────────────────────────────────

    def add_message(self, conv_id: str, role: str, content: str) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = self._client.table("messages").insert({
                "conversation_id": conv_id, "role": role, "content": content,
            }).execute()
            self.update_conversation(conv_id)
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase add_message: {e}")
            return None

    def get_recent_messages(self, conv_id: str, limit: int = 10) -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("messages").select("*")
                      .eq("conversation_id", conv_id)
                      .order("created_at", desc=True).limit(limit).execute())
            data = result.data or []
            data.reverse()
            return data
        except Exception as e:
            logger.error(f"supabase get_recent_messages: {e}")
            return []

    def get_messages_page(self, conv_id: str, offset: int = 0,
                          limit: int = 20) -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("messages").select("*")
                      .eq("conversation_id", conv_id)
                      .order("created_at", desc=True)
                      .range(offset, offset + limit - 1).execute())
            data = result.data or []
            data.reverse()
            return data
        except Exception as e:
            logger.error(f"supabase get_messages_page: {e}")
            return []

    def get_message_count(self, conv_id: str) -> int:
        if not self.available:
            return 0
        try:
            result = (self._client.table("messages")
                      .select("id", count="exact")
                      .eq("conversation_id", conv_id).execute())
            return result.count or 0
        except Exception as e:
            logger.error(f"supabase get_message_count: {e}")
            return 0

    # ── Tasks ─────────────────────────────────────────────────

    def create_task(self, title: str, conv_id: str = None,
                    user_id: str = "local", status: str = "active") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            row = {"title": title, "user_id": user_id, "status": status}
            if conv_id:
                row["conversation_id"] = conv_id
            result = self._client.table("tasks").insert(row).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase create_task: {e}")
            return None

    def get_tasks(self, user_id: str = "local") -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("tasks").select("*")
                      .eq("user_id", user_id)
                      .order("created_at", desc=True).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_tasks: {e}")
            return []

    def update_task(self, task_id: str, **fields) -> bool:
        if not self.available:
            return False
        try:
            fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._client.table("tasks").update(fields).eq("id", task_id).execute()
            return True
        except Exception as e:
            logger.error(f"supabase update_task: {e}")
            return False

    # ── Events ────────────────────────────────────────────────

    def log_event(self, event_type: str, content: str,
                  conv_id: str = None, user_id: str = "local") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            row = {"event_type": event_type, "content": content, "user_id": user_id}
            if conv_id:
                row["conversation_id"] = conv_id
            result = self._client.table("events").insert(row).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase log_event: {e}")
            return None

    def get_events(self, user_id: str = "local", limit: int = 50) -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("events").select("*")
                      .eq("user_id", user_id)
                      .order("created_at", desc=True).limit(limit).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_events: {e}")
            return []

    # ── Files ─────────────────────────────────────────────────

    def register_file(self, name: str, path: str, size: int,
                      content_type: str = "", conv_id: str = None,
                      user_id: str = "local") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            row = {"name": name, "path": path, "size": size,
                   "content_type": content_type, "user_id": user_id}
            if conv_id:
                row["conversation_id"] = conv_id
            result = self._client.table("files").insert(row).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase register_file: {e}")
            return None

    def get_files(self, user_id: str = "local", conv_id: str = None) -> List[Dict]:
        if not self.available:
            return []
        try:
            q = self._client.table("files").select("*").eq("user_id", user_id)
            if conv_id:
                q = q.eq("conversation_id", conv_id)
            result = q.order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_files: {e}")
            return []

    # ── Agent State ───────────────────────────────────────────

    def get_agent_state(self, agent_id: str = "onyx") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = (self._client.table("agent_state").select("*")
                      .eq("agent_id", agent_id).single().execute())
            return result.data
        except Exception as e:
            logger.error(f"supabase get_agent_state: {e}")
            return None

    def upsert_agent_state(self, agent_id: str = "onyx", **fields) -> bool:
        if not self.available:
            return False
        try:
            fields["agent_id"] = agent_id
            fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._client.table("agent_state").upsert(
                fields, on_conflict="agent_id"
            ).execute()
            return True
        except Exception as e:
            logger.error(f"supabase upsert_agent_state: {e}")
            return False

    # ── Memories ──────────────────────────────────────────────

    def add_memory(self, content: str, user_id: str = "local",
                   conv_id: str = None, memory_type: str = "fact") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            row = {"content": content, "user_id": user_id,
                   "memory_type": memory_type}
            if conv_id:
                row["conversation_id"] = conv_id
            result = self._client.table("memories").insert(row).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase add_memory: {e}")
            return None

    def get_memories(self, user_id: str = "local", limit: int = 10) -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("memories").select("*")
                      .eq("user_id", user_id)
                      .order("created_at", desc=True).limit(limit).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_memories: {e}")
            return []

    # ── Beliefs ───────────────────────────────────────────────

    def add_belief(self, content: str, confidence: float = 0.8,
                   user_id: str = "local") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = self._client.table("beliefs").insert({
                "content": content, "confidence": confidence,
                "user_id": user_id,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase add_belief: {e}")
            return None

    def get_beliefs(self, user_id: str = "local") -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("beliefs").select("*")
                      .eq("user_id", user_id)
                      .order("confidence", desc=True).limit(15).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_beliefs: {e}")
            return []

    # ── Goals ─────────────────────────────────────────────────

    def add_goal(self, title: str, user_id: str = "local",
                 status: str = "active") -> Optional[Dict]:
        if not self.available:
            return None
        try:
            result = self._client.table("goals").insert({
                "title": title, "user_id": user_id, "status": status,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"supabase add_goal: {e}")
            return None

    def get_goals(self, user_id: str = "local") -> List[Dict]:
        if not self.available:
            return []
        try:
            result = (self._client.table("goals").select("*")
                      .eq("user_id", user_id)
                      .order("created_at", desc=True).limit(10).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"supabase get_goals: {e}")
            return []

    def update_goal(self, goal_id: str, **fields) -> bool:
        if not self.available:
            return False
        try:
            fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._client.table("goals").update(fields).eq("id", goal_id).execute()
            return True
        except Exception as e:
            logger.error(f"supabase update_goal: {e}")
            return False
