"""Chat service — sends messages through Letta. Nothing else.

Letta = brain (memory, identity, compaction, tools, model calls).
This service = thin relay that mirrors results to local SQLite for UI display.
No prompt building. No transcript replay. No local tools. No fallback brain.
"""
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

# (display_name, letta_model_id, description) — for UI model selector
ANTHROPIC_MODELS = [
    ("Sonnet 4.6",    "anthropic/claude-sonnet-4-6",           "Fast + smart — best all-rounder"),
    ("Opus 4.6",      "anthropic/claude-opus-4-6",             "Most capable — deep reasoning"),
    ("Sonnet 4.5",    "anthropic/claude-sonnet-4-5-20250514",  "Previous balanced model"),
    ("Opus 4.5",      "anthropic/claude-opus-4-5-20250514",    "Previous flagship"),
    ("Haiku 4.5",     "anthropic/claude-haiku-4-5-20251001",   "Fast + cheap"),
    ("Sonnet 4",      "anthropic/claude-sonnet-4-20250514",    "Balanced"),
    ("Opus 4",        "anthropic/claude-opus-4-20250514",      "Powerful reasoning"),
    ("Sonnet 3.5 v2", "anthropic/claude-3-5-sonnet-20241022",  "Proven workhorse"),
    ("Sonnet 3.5",    "anthropic/claude-3-5-sonnet-20240620",  "Original 3.5"),
    ("Haiku 3.5",     "anthropic/claude-3-5-haiku-20241022",   "Ultra-fast"),
    ("Opus 3",        "anthropic/claude-3-opus-20240229",      "Legacy flagship"),
    ("Sonnet 3",      "anthropic/claude-3-sonnet-20240229",    "Legacy balanced"),
    ("Haiku 3",       "anthropic/claude-3-haiku-20240307",     "Legacy fast"),
]


class ChatService:
    """Thin relay: UI message -> Letta bridge -> mirror to SQLite."""

    def __init__(self, storage=None, bridge=None):
        self.storage = storage or StorageService()
        self.bridge = bridge

        settings = self.storage.get_settings()
        model_cfg = settings.get("model", {})
        self.model_name = model_cfg.get("name", "anthropic/claude-sonnet-4-6")
        self._active_chat_id = None

    @property
    def runtime_name(self) -> str:
        if self.bridge and self.bridge.agent_ready:
            return "letta"
        return "not_configured"

    def set_model(self, model_name: str):
        self.model_name = model_name
        settings = self.storage.get_settings()
        settings.setdefault("model", {})["name"] = model_name
        self.storage.save_settings(settings)
        logger.info(f"Model changed to {model_name}")

    def switch_chat(self, chat_id: int):
        self._active_chat_id = chat_id

    async def send_message(self, message: str, chat_id: int,
                           on_tool_output=None, cancel_flag=None) -> str:
        """Send user message to Letta. Mirror both sides to local SQLite.

        The ONLY payload sent to Letta is the user's text.
        No transcript. No persona. No prompt assembly. Letta handles all of that.
        """
        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Mirror user message to local SQLite (for UI display only)
        self.storage.add_message(chat_id, "user", message)

        if not (self.bridge and self.bridge.agent_ready):
            error_msg = (
                "Letta is not configured. ONYX requires a running Letta server.\n\n"
                "1. docker run -d -p 8283:8283 "
                "-e LETTA_ANTHROPIC_API_KEY=your_key lettaai/letta:latest\n"
                "2. Set LETTA_BASE_URL=http://localhost:8283 in .env\n"
                "3. Restart ONYX"
            )
            logger.warning(f"[{self.runtime_name}] Letta not ready")
            self.storage.add_message(chat_id, "assistant", error_msg)
            return error_msg

        # Send ONLY the new message text to Letta. That's it.
        logger.info(f"[letta] -> agent (chat {chat_id})")
        result = self.bridge.send_message(text=message, cancel_flag=cancel_flag)

        if cancel_flag and cancel_flag.is_set():
            return ""

        response = result.get("response", "")

        # Surface tool calls to UI
        for tc in result.get("tool_calls", []):
            if on_tool_output:
                on_tool_output(
                    tc.get("name", "tool"),
                    tc.get("arguments", "")[:200],
                    tc.get("result", "")[:2000],
                )

        # Mirror assistant response to local SQLite (for UI display only)
        if response:
            self.storage.add_message(chat_id, "assistant", response)

        return response
