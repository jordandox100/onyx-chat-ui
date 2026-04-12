"""Chat service — relay with safety filter, subscription limits, tool restrictions."""
from desktop_app.services.storage_service import StorageService
from desktop_app.services.safety_filter import is_blocked, BLOCK_MESSAGE
from desktop_app.utils.logger import get_logger

logger = get_logger()

ANTHROPIC_MODELS = [
    ("Sonnet 4.6",    "claude-sonnet-4-6",           "Fast + smart"),
    ("Opus 4.6",      "claude-opus-4-6",             "Most capable"),
    ("Sonnet 4.5",    "claude-sonnet-4-5-20250514",  "Previous balanced"),
    ("Opus 4.5",      "claude-opus-4-5-20250514",    "Previous flagship"),
    ("Haiku 4.5",     "claude-haiku-4-5-20251001",   "Fast + cheap"),
    ("Sonnet 4",      "claude-sonnet-4-20250514",    "Balanced"),
    ("Opus 4",        "claude-opus-4-20250514",      "Powerful"),
    ("Sonnet 3.5 v2", "claude-3-5-sonnet-20241022",  "Proven workhorse"),
    ("Sonnet 3.5",    "claude-3-5-sonnet-20240620",  "Original 3.5"),
    ("Haiku 3.5",     "claude-3-5-haiku-20241022",   "Ultra-fast"),
    ("Opus 3",        "claude-3-opus-20240229",      "Legacy flagship"),
    ("Sonnet 3",      "claude-3-sonnet-20240229",    "Legacy balanced"),
    ("Haiku 3",       "claude-3-haiku-20240307",     "Legacy fast"),
]


class ChatService:
    def __init__(self, storage=None, runtime=None):
        self.storage = storage or StorageService()
        self.runtime = runtime
        self._is_admin = False
        self._username = "local"
        self._subs = None
        settings = self.storage.get_settings()
        self.model_name = settings.get("model", {}).get("name", "claude-sonnet-4-6")
        self._active_chat_id = None

    def set_admin(self, is_admin: bool):
        self._is_admin = is_admin

    def set_user(self, username: str, subs=None):
        self._username = username
        self._subs = subs

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

    def switch_chat(self, chat_id: int):
        self._active_chat_id = chat_id

    async def send_message(self, message: str, chat_id: int,
                           on_tool_output=None, cancel_flag=None) -> str:
        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Mirror locally
        self.storage.add_message(chat_id, "user", message)

        # Safety filter (admin bypasses)
        if not self._is_admin and is_blocked(message):
            logger.warning("[safety] blocked")
            self.storage.add_message(chat_id, "assistant", BLOCK_MESSAGE)
            return BLOCK_MESSAGE

        # Message limit check (admin bypasses)
        if not self._is_admin and self._subs:
            allowed, reason = self._subs.can_send_message(self._username)
            if not allowed:
                self.storage.add_message(chat_id, "assistant", reason)
                return reason
            self._subs.record_message(self._username)

        if not (self.runtime and self.runtime.available):
            error_msg = (
                "ONYX is not configured.\n\n"
                "Set ANTHROPIC_API_KEY in .env and restart."
            )
            self.storage.add_message(chat_id, "assistant", error_msg)
            return error_msg

        local_msgs = self.storage.get_chat_messages(chat_id)

        # Get allowed tools for user's subscription tier
        allowed_tools = None
        if self._subs and not self._is_admin:
            allowed_tools = self._subs.get_allowed_tools(self._username)

        result = self.runtime.send_message(
            text=message,
            conversation_id=chat_id,
            local_messages=local_msgs,
            allowed_tools=allowed_tools,
            username=self._username,
        )

        if cancel_flag and cancel_flag.is_set():
            return ""

        route = result.get("route", "?")
        tools_used = result.get("tools_used", [])
        logger.info(f"[chat] route={route}, tools={tools_used or 'none'}")

        # Deduct builder tokens for tool use
        if tools_used and self._subs:
            tier = self._subs.get_user_tier(self._username)
            if tier == "builder":
                self._subs.use_token(self._username, len(tools_used))

        response = result.get("response", "")
        if response:
            self.storage.add_message(chat_id, "assistant", response)

        for tc in result.get("tool_calls", []):
            if on_tool_output:
                on_tool_output(
                    tc.get("name", "tool"),
                    tc.get("arguments", "")[:200],
                    tc.get("result", "")[:2000],
                )

        return response
