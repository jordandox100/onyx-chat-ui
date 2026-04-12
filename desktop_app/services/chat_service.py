"""Chat service — relay between UI and OnyxRuntime.

Mirrors messages to local SQLite for UI display.
The runtime handles: Anthropic calls, Supabase state, compact prompts.
No Letta. No transcript replay.
"""
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

# (display_name, model_id, description)
ANTHROPIC_MODELS = [
    ("Sonnet 4.6",    "claude-sonnet-4-6",           "Fast + smart — best all-rounder"),
    ("Opus 4.6",      "claude-opus-4-6",             "Most capable — deep reasoning"),
    ("Sonnet 4.5",    "claude-sonnet-4-5-20250514",  "Previous balanced model"),
    ("Opus 4.5",      "claude-opus-4-5-20250514",    "Previous flagship"),
    ("Haiku 4.5",     "claude-haiku-4-5-20251001",   "Fast + cheap"),
    ("Sonnet 4",      "claude-sonnet-4-20250514",    "Balanced"),
    ("Opus 4",        "claude-opus-4-20250514",      "Powerful reasoning"),
    ("Sonnet 3.5 v2", "claude-3-5-sonnet-20241022",  "Proven workhorse"),
    ("Sonnet 3.5",    "claude-3-5-sonnet-20240620",  "Original 3.5"),
    ("Haiku 3.5",     "claude-3-5-haiku-20241022",   "Ultra-fast"),
    ("Opus 3",        "claude-3-opus-20240229",      "Legacy flagship"),
    ("Sonnet 3",      "claude-3-sonnet-20240229",    "Legacy balanced"),
    ("Haiku 3",       "claude-3-haiku-20240307",     "Legacy fast"),
]


class ChatService:
    """UI -> Runtime -> SQLite mirror."""

    def __init__(self, storage=None, runtime=None):
        self.storage = storage or StorageService()
        self.runtime = runtime
        settings = self.storage.get_settings()
        self.model_name = settings.get("model", {}).get("name", "claude-sonnet-4-6")
        self._active_chat_id = None

    @property
    def runtime_name(self) -> str:
        if self.runtime and self.runtime.available:
            return "supabase+anthropic"
        return "not_configured"

    def set_model(self, model_name: str):
        self.model_name = model_name
        if self.runtime:
            self.runtime.set_model(model_name)
        settings = self.storage.get_settings()
        settings.setdefault("model", {})["name"] = model_name
        self.storage.save_settings(settings)
        logger.info(f"Model changed to {model_name}")

    def switch_chat(self, chat_id: int):
        self._active_chat_id = chat_id

    async def send_message(self, message: str, chat_id: int,
                           on_tool_output=None, cancel_flag=None) -> str:
        """Send user message through runtime. Mirror to local SQLite."""
        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Mirror user message locally
        self.storage.add_message(chat_id, "user", message)

        if not (self.runtime and self.runtime.available):
            error_msg = (
                "ONYX is not configured.\n\n"
                "Set ANTHROPIC_API_KEY in .env and restart.\n"
                "Optionally set SUPABASE_URL + SUPABASE_ANON_KEY for persistent memory."
            )
            self.storage.add_message(chat_id, "assistant", error_msg)
            return error_msg

        # Get local messages as fallback context if Supabase isn't available
        local_msgs = self.storage.get_chat_messages(chat_id)

        logger.info(f"[{self.runtime_name}] -> model (chat {chat_id})")
        result = self.runtime.send_message(
            text=message,
            conversation_id=chat_id,
            local_messages=local_msgs,
        )

        if cancel_flag and cancel_flag.is_set():
            return ""

        route = result.get("route", "?")
        tools_used = result.get("tools_used", [])
        logger.info(f"[chat] route={route}, tools={tools_used or 'none'}")

        response = result.get("response", "")
        if response:
            self.storage.add_message(chat_id, "assistant", response)

        # Emit tool call info to UI if present
        for tc in result.get("tool_calls", []):
            if on_tool_output:
                on_tool_output(
                    tc.get("name", "tool"),
                    tc.get("arguments", "")[:200],
                    tc.get("result", "")[:2000],
                )

        return response
