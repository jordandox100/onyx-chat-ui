"""Letta bridge — real Letta client integration for persistent agent runtime.

Letta is the primary runtime for ONYX: chat, memory, identity, continuity, compaction.
Anthropic is the model provider BEHIND Letta (configured on the Letta server).
Supabase mirrors app-visible state for the inspector/UI.

Env vars:
    LETTA_BASE_URL   — Letta server URL (e.g. http://localhost:8283)
    LETTA_API_KEY    — Letta API key (for Letta Cloud; optional for self-hosted)
    LETTA_AGENT_ID   — Pre-existing agent ID (optional; auto-creates if missing)
"""
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timezone

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    from letta_client import Letta
    LETTA_SDK_AVAILABLE = True
except ImportError:
    LETTA_SDK_AVAILABLE = False
    Letta = None

# Default ONYX persona and human memory blocks
ONYX_PERSONA = (
    "My name is ONYX. I am a persistent AI assistant running on the user's "
    "Linux desktop. I am sharp, direct, technically savvy, and genuinely helpful. "
    "I remember context across sessions through my persistent memory. "
    "I have access to the user's filesystem and shell via tools."
)
ONYX_HUMAN = (
    "The human is a power user who values directness and technical precision. "
    "Update this block as you learn more about them."
)

# Letta model string for Anthropic Claude (configured on Letta server)
DEFAULT_LETTA_MODEL = "anthropic/claude-sonnet-4-6"
DEFAULT_EMBEDDING = "letta/letta-free"


class LettaBridge:
    """Bridge between UI and Letta agent runtime.

    Lifecycle:
      1. __init__ reads env vars and connects to Letta
      2. ensure_agent() creates or retrieves the ONYX agent
      3. send_message() routes user input through Letta (persistent memory)
      4. Inspector polls get_agent_state(), get_memory_blocks(), etc.

    If LETTA_BASE_URL is not set, the bridge enters NOT_CONFIGURED state
    and all methods return clean errors/defaults.
    """

    class Status:
        NOT_INSTALLED = "NOT_INSTALLED"
        NOT_CONFIGURED = "NOT_CONFIGURED"
        CONNECTING = "CONNECTING"
        CONNECTED = "CONNECTED"
        ERROR = "ERROR"
        AGENT_READY = "AGENT_READY"

    def __init__(self, supabase=None, storage=None):
        self.supabase = supabase
        self.storage = storage  # local SQLite for fallback display
        self._client: Optional[Letta] = None
        self._agent_id: Optional[str] = None
        self._status = self.Status.NOT_CONFIGURED
        self._status_detail = ""
        self._lock = threading.Lock()
        self._model = DEFAULT_LETTA_MODEL

        self._connect()

    # ── Connection & Health ───────────────────────────────────

    def _connect(self):
        if not LETTA_SDK_AVAILABLE:
            self._status = self.Status.NOT_INSTALLED
            self._status_detail = "letta-client not installed (pip install letta-client)"
            logger.warning(self._status_detail)
            return

        base_url = os.environ.get("LETTA_BASE_URL", "").strip()
        api_key = os.environ.get("LETTA_API_KEY", "").strip()

        if not base_url:
            self._status = self.Status.NOT_CONFIGURED
            self._status_detail = "LETTA_BASE_URL not set"
            logger.info("Letta not configured. Set LETTA_BASE_URL in .env")
            return

        self._status = self.Status.CONNECTING
        try:
            kwargs = {"base_url": base_url}
            if api_key:
                kwargs["api_key"] = api_key
            self._client = Letta(**kwargs)
            self._status = self.Status.CONNECTED
            self._status_detail = f"Connected to {base_url}"
            logger.info(f"Letta connected: {base_url}")
        except Exception as e:
            self._status = self.Status.ERROR
            self._status_detail = f"Connection failed: {e}"
            logger.error(f"Letta connection error: {e}")

    @property
    def available(self) -> bool:
        return self._client is not None and self._status in (
            self.Status.CONNECTED, self.Status.AGENT_READY
        )

    @property
    def agent_ready(self) -> bool:
        return self._status == self.Status.AGENT_READY and self._agent_id is not None

    @property
    def status(self) -> str:
        return self._status

    @property
    def status_detail(self) -> str:
        return self._status_detail

    @property
    def agent_id(self) -> Optional[str]:
        return self._agent_id

    def health_check(self) -> dict:
        """Check Letta server health. Returns {"ok": bool, "detail": str}."""
        if not self.available:
            return {"ok": False, "detail": self._status_detail}
        try:
            # Try listing agents as a health probe
            self._client.agents.list(limit=1)
            return {"ok": True, "detail": "Letta server healthy"}
        except Exception as e:
            return {"ok": False, "detail": str(e)}

    # ── Agent Management ──────────────────────────────────────

    def ensure_agent(self, model: str = None) -> bool:
        """Create or retrieve the ONYX agent. Returns True if agent is ready."""
        if not self.available:
            logger.warning(f"Cannot ensure agent: {self._status_detail}")
            return False

        self._model = model or DEFAULT_LETTA_MODEL

        # Check for pre-configured agent ID
        env_agent_id = os.environ.get("LETTA_AGENT_ID", "").strip()
        if env_agent_id:
            try:
                agent = self._client.agents.retrieve(agent_id=env_agent_id)
                self._agent_id = agent.id
                self._status = self.Status.AGENT_READY
                self._status_detail = f"Agent loaded: {agent.name} ({agent.id})"
                logger.info(f"Letta agent loaded: {agent.name} ({agent.id})")
                return True
            except Exception as e:
                logger.warning(f"LETTA_AGENT_ID '{env_agent_id}' not found: {e}")

        # Search for existing ONYX agent
        try:
            existing = self._client.agents.list(limit=50)
            for agent in existing:
                if agent.name == "ONYX":
                    self._agent_id = agent.id
                    self._status = self.Status.AGENT_READY
                    self._status_detail = f"Agent found: ONYX ({agent.id})"
                    logger.info(f"Found existing ONYX agent: {agent.id}")
                    return True
        except Exception as e:
            logger.error(f"Error searching for agents: {e}")

        # Create new ONYX agent
        return self._create_agent()

    def _create_agent(self) -> bool:
        """Create a fresh ONYX agent on the Letta server."""
        try:
            persona_text = ONYX_PERSONA
            human_text = ONYX_HUMAN

            # Load custom personality from local config if available
            if self.storage:
                custom = self.storage.get_personality()
                if custom and "ONYX" in custom:
                    persona_text = custom

            agent = self._client.agents.create(
                name="ONYX",
                model=self._model,
                embedding=DEFAULT_EMBEDDING,
                memory_blocks=[
                    {"label": "persona", "value": persona_text},
                    {"label": "human", "value": human_text},
                ],
                include_base_tools=True,
            )
            self._agent_id = agent.id
            self._status = self.Status.AGENT_READY
            self._status_detail = f"Agent created: ONYX ({agent.id})"
            logger.info(f"Created ONYX agent: {agent.id}")
            return True
        except Exception as e:
            self._status = self.Status.ERROR
            self._status_detail = f"Agent creation failed: {e}"
            logger.error(f"Failed to create ONYX agent: {e}")
            return False

    # ── Chat ──────────────────────────────────────────────────

    def send_message(self, text: str, cancel_flag=None) -> dict:
        """Send a message to ONYX via Letta.

        Returns:
            {
                "response": str,          # assistant text
                "reasoning": str,         # reasoning trace (if available)
                "tool_calls": list,       # tool call info
                "usage": dict,            # token usage
                "raw_messages": list,     # all message objects
            }
        """
        if not self.agent_ready:
            return {
                "response": f"[Letta not ready: {self._status_detail}]",
                "reasoning": "", "tool_calls": [], "usage": {},
                "raw_messages": [],
            }

        logger.info(f"Sending to Letta agent {self._agent_id}: {text[:80]}...")

        try:
            response = self._client.agents.messages.create(
                agent_id=self._agent_id,
                messages=[{"role": "user", "content": text}],
            )

            result = {
                "response": "",
                "reasoning": "",
                "tool_calls": [],
                "usage": {},
                "raw_messages": [],
            }

            if hasattr(response, "usage") and response.usage:
                result["usage"] = {
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            for msg in (response.messages or []):
                mt = getattr(msg, "message_type", "")
                result["raw_messages"].append({
                    "type": mt,
                    "content": getattr(msg, "content", ""),
                })

                if mt == "assistant_message":
                    result["response"] = getattr(msg, "content", "")
                elif mt == "reasoning_message":
                    result["reasoning"] = getattr(msg, "reasoning", "")
                elif mt == "tool_call_message":
                    tc = getattr(msg, "tool_call", None)
                    if tc:
                        result["tool_calls"].append({
                            "name": getattr(tc, "name", "?"),
                            "arguments": getattr(tc, "arguments", ""),
                        })
                elif mt == "tool_return_message":
                    tr = getattr(msg, "tool_return", "")
                    if result["tool_calls"]:
                        result["tool_calls"][-1]["result"] = tr

            if not result["response"]:
                # Fallback: concatenate any text content
                texts = [
                    getattr(m, "content", "")
                    for m in (response.messages or [])
                    if getattr(m, "content", "")
                ]
                result["response"] = "\n".join(texts) or "[No response from agent]"

            logger.info(
                f"Letta response: {len(result['response'])} chars, "
                f"{len(result['tool_calls'])} tool calls, "
                f"tokens={result['usage']}"
            )
            return result

        except Exception as e:
            logger.error(f"Letta send_message error: {e}")
            return {
                "response": f"[Letta error: {e}]",
                "reasoning": "", "tool_calls": [], "usage": {},
                "raw_messages": [],
            }

    def send_message_streaming(self, text: str):
        """Generator that yields Letta response chunks for streaming display."""
        if not self.agent_ready:
            yield {"type": "error", "content": f"Letta not ready: {self._status_detail}"}
            return

        try:
            stream = self._client.agents.messages.stream(
                agent_id=self._agent_id,
                messages=[{"role": "user", "content": text}],
                stream_tokens=True,
            )
            for chunk in stream:
                mt = getattr(chunk, "message_type", "")
                if mt == "assistant_message":
                    yield {"type": "assistant", "content": getattr(chunk, "content", "")}
                elif mt == "reasoning_message":
                    yield {"type": "reasoning", "content": getattr(chunk, "reasoning", "")}
                elif mt == "tool_call_message":
                    tc = getattr(chunk, "tool_call", None)
                    if tc:
                        yield {
                            "type": "tool_call",
                            "name": getattr(tc, "name", ""),
                            "arguments": getattr(tc, "arguments", ""),
                        }
                elif mt == "tool_return_message":
                    yield {"type": "tool_return", "content": getattr(chunk, "tool_return", "")}
        except Exception as e:
            logger.error(f"Letta streaming error: {e}")
            yield {"type": "error", "content": str(e)}

    # ── Agent State & Memory ──────────────────────────────────

    def get_agent_state(self) -> dict:
        """Get agent metadata from Letta server."""
        state = {
            "agent_id": self._agent_id or "none",
            "status": self._status,
            "status_detail": self._status_detail,
            "model": self._model,
            "name": "ONYX",
        }
        if not self.agent_ready:
            return state
        try:
            agent = self._client.agents.retrieve(agent_id=self._agent_id)
            state["name"] = agent.name or "ONYX"
            state["model"] = getattr(agent, "model", self._model) or self._model
            state["created_at"] = str(getattr(agent, "created_at", ""))
            state["message_ids_count"] = len(getattr(agent, "message_ids", []) or [])
        except Exception as e:
            logger.error(f"get_agent_state error: {e}")
        return state

    def get_memory_blocks(self) -> List[Dict]:
        """Get all memory blocks from the Letta agent."""
        if not self.agent_ready:
            return []
        try:
            blocks = self._client.agents.blocks.list(agent_id=self._agent_id)
            return [
                {
                    "label": getattr(b, "label", "?"),
                    "value": getattr(b, "value", ""),
                    "id": getattr(b, "id", ""),
                    "limit": getattr(b, "limit", 0),
                }
                for b in blocks
            ]
        except Exception as e:
            logger.error(f"get_memory_blocks error: {e}")
            return []

    def get_memory_block(self, label: str) -> Optional[str]:
        """Get a specific memory block by label."""
        if not self.agent_ready:
            return None
        try:
            block = self._client.agents.blocks.retrieve(
                agent_id=self._agent_id, block_label=label
            )
            return getattr(block, "value", "")
        except Exception as e:
            logger.error(f"get_memory_block '{label}' error: {e}")
            return None

    def get_conversation_messages(self, limit: int = 50) -> List[Dict]:
        """Get recent messages from Letta's conversation history."""
        if not self.agent_ready:
            return []
        try:
            msgs = self._client.agents.messages.list(
                agent_id=self._agent_id, limit=limit
            )
            result = []
            for m in msgs:
                mt = getattr(m, "message_type", "")
                content = getattr(m, "content", "")
                if mt in ("user_message", "assistant_message"):
                    result.append({
                        "role": "user" if mt == "user_message" else "assistant",
                        "content": content,
                        "created_at": str(getattr(m, "created_at", "")),
                    })
            return result
        except Exception as e:
            logger.error(f"get_conversation_messages error: {e}")
            return []

    # ── Tasks (Supabase) ──────────────────────────────────────

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

    # ── Events (Supabase) ─────────────────────────────────────

    def get_events(self, user_id: str = "local", limit: int = 50) -> List[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.get_events(user_id, limit)
        return []

    def log_event(self, event_type: str, content: str,
                  conv_id: str = None) -> Optional[Dict]:
        if self.supabase and self.supabase.available:
            return self.supabase.log_event(event_type, content, conv_id)
        return None

    # ── Files (Supabase) ──────────────────────────────────────

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
