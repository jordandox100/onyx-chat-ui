"""Chat service — routes through Letta agent runtime.

Letta is the primary runtime (persistent memory, identity, compaction).
Anthropic is the model provider configured on the Letta server.
Direct Anthropic SDK is NOT used as a normal chat path.

If Letta is not configured, returns a clean "not configured" error.
Local SQLite is used for UI-visible history mirroring only.
"""
import os
from dotenv import load_dotenv

from desktop_app.services.storage_service import StorageService
from desktop_app.services.tool_service import ToolService
from desktop_app.utils.logger import get_logger

load_dotenv()
logger = get_logger()

# (display_name, model_id, description)  — used for Letta model selection
ANTHROPIC_MODELS = [
    ("Sonnet 4.6",    "anthropic/claude-sonnet-4-6",           "Fast + smart — best all-rounder for daily tasks"),
    ("Opus 4.6",      "anthropic/claude-opus-4-6",             "Most capable — deep reasoning, analysis, creative writing"),
    ("Sonnet 4.5",    "anthropic/claude-sonnet-4-5-20250514",  "Previous balanced model — reliable general use"),
    ("Opus 4.5",      "anthropic/claude-opus-4-5-20250514",    "Previous flagship — extended thinking, hard problems"),
    ("Haiku 4.5",     "anthropic/claude-haiku-4-5-20251001",   "Fast + cheap — quick answers, summaries, simple Q&A"),
    ("Sonnet 4",      "anthropic/claude-sonnet-4-20250514",    "Balanced — good coding, writing, analysis"),
    ("Opus 4",        "anthropic/claude-opus-4-20250514",      "Powerful — complex multi-step reasoning"),
    ("Sonnet 3.5 v2", "anthropic/claude-3-5-sonnet-20241022",  "Proven workhorse — coding, writing, analysis"),
    ("Sonnet 3.5",    "anthropic/claude-3-5-sonnet-20240620",  "Original 3.5 — fast, strong at coding"),
    ("Haiku 3.5",     "anthropic/claude-3-5-haiku-20241022",   "Ultra-fast — near-instant responses, low cost"),
    ("Opus 3",        "anthropic/claude-3-opus-20240229",      "Legacy flagship — still strong for complex tasks"),
    ("Sonnet 3",      "anthropic/claude-3-sonnet-20240229",    "Legacy balanced — reliable older model"),
    ("Haiku 3",       "anthropic/claude-3-haiku-20240307",     "Legacy fast — minimal latency, basic tasks"),
]


class ChatService:
    """Routes messages through Letta bridge. Mirrors history to local SQLite."""

    def __init__(self, storage=None, bridge=None):
        self.storage = storage or StorageService()
        self.bridge = bridge
        self.tool_service = ToolService()

        settings = self.storage.get_settings()
        model_cfg = settings.get("model", {})
        self.model_name = model_cfg.get("name", "anthropic/claude-sonnet-4-6")

        self._active_chat_id = None

    @property
    def runtime_name(self) -> str:
        """Which runtime is handling messages."""
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
        """Send message through Letta runtime.

        Flow:
        1. Persist user message to local SQLite (for UI display)
        2. Send to Letta agent (handles memory, identity, compaction)
        3. Persist assistant response to local SQLite
        4. Return response text
        """
        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Mirror user message to local storage
        self.storage.add_message(chat_id, "user", message)

        # Route through Letta
        if self.bridge and self.bridge.agent_ready:
            logger.info(f"[letta] Sending message to agent (chat {chat_id})")
            result = self.bridge.send_message(text=message, cancel_flag=cancel_flag)

            if cancel_flag and cancel_flag.is_set():
                return ""

            response = result.get("response", "")

            # Emit tool outputs to UI if present
            for tc in result.get("tool_calls", []):
                if on_tool_output:
                    on_tool_output(
                        tc.get("name", "tool"),
                        tc.get("arguments", "")[:200],
                        tc.get("result", "")[:2000],
                    )

            # Mirror assistant response to local storage
            if response:
                self.storage.add_message(chat_id, "assistant", response)

            return response

        else:
            # Letta not configured — return clear error
            error_msg = (
                "Letta is not configured. ONYX requires a running Letta server.\n\n"
                "Setup:\n"
                "1. Run: docker run -d -p 8283:8283 "
                "-e LETTA_ANTHROPIC_API_KEY=your_key lettaai/letta:latest\n"
                "2. Set in .env:\n"
                "   LETTA_BASE_URL=http://localhost:8283\n"
                "   LETTA_API_KEY=  (optional for self-hosted)\n"
                "3. Restart ONYX"
            )
            logger.warning("[not_configured] Letta bridge not ready")
            self.storage.add_message(chat_id, "assistant", error_msg)
            return error_msg
