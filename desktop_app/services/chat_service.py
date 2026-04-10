"""Chat service — Claude Opus/Sonnet via emergentintegrations with tool support"""
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv

from desktop_app.services.storage_service import StorageService
from desktop_app.services.tool_service import ToolService
from desktop_app.utils.logger import get_logger

load_dotenv()
logger = get_logger()

ANTHROPIC_MODELS = [
    ("Sonnet 4.6",  "claude-sonnet-4-6"),
    ("Opus 4.6",    "claude-opus-4-6"),
    ("Sonnet 4.5",  "claude-sonnet-4-5"),
    ("Opus 4.5",    "claude-opus-4-5"),
    ("Haiku 4.5",   "claude-haiku-4-5"),
    ("Sonnet 4",    "claude-sonnet-4"),
    ("Opus 4",      "claude-opus-4"),
    ("Sonnet 3.5",  "claude-3-5-sonnet"),
    ("Haiku 3.5",   "claude-3-5-haiku"),
]


class ChatService:
    def __init__(self):
        self.storage = StorageService()
        self.tool_service = ToolService()
        self.api_key = os.getenv("CLAUDE_API_KEY", "").strip()

        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not set — AI chat will not work.")

        settings = self.storage.get_settings()
        model_cfg = settings.get("model", {})
        self.provider = model_cfg.get("provider", "anthropic")
        self.model_name = model_cfg.get("name", "claude-sonnet-4-6")

        self._system_message = self._build_system_message()
        self._active_chat_id = None
        self._init_llm()

    def _build_system_message(self) -> str:
        base = self.storage.build_system_message()
        tools = self.tool_service.get_tools_prompt()
        return f"{base}\n{tools}"

    def _init_llm(self, session_id: str = "onyx_default"):
        self.llm_chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._system_message,
        )
        self.llm_chat.with_model(self.provider, self.model_name)

    def set_model(self, model_name: str):
        self.model_name = model_name
        settings = self.storage.get_settings()
        settings.setdefault("model", {})["name"] = model_name
        self.storage.save_settings(settings)
        self._init_llm(session_id=f"onyx_{self._active_chat_id or 'default'}")
        logger.info(f"Model changed to {model_name}")

    def switch_chat(self, chat_id: int):
        """Create a fresh LLM session for this chat."""
        self._active_chat_id = chat_id
        self._system_message = self._build_system_message()
        self._init_llm(session_id=f"onyx_chat_{chat_id}")

    def reload_config(self):
        self._system_message = self._build_system_message()
        self._init_llm(session_id=f"onyx_{self._active_chat_id or 'default'}")
        logger.info("Config reloaded")

    async def send_message(self, message: str, chat_id: int,
                           on_tool_output=None) -> str:
        if not self.api_key:
            return "No API key configured. Add CLAUDE_API_KEY to .env."

        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Build context from history
        history = self.storage.get_chat_messages(chat_id)
        full_msg = self._build_contextual_message(history, message)

        self.storage.add_message(chat_id, "user", message)

        # Send with tool loop
        response = await self._send_with_tools(full_msg, on_tool_output)

        # Store clean response
        clean = ToolService.strip_tool_tags(response)
        self.storage.add_message(chat_id, "assistant", clean)
        return clean

    def _build_contextual_message(self, history, new_message: str) -> str:
        if not history:
            return new_message

        lines = ["[Previous conversation — continue naturally]\n"]
        for m in history[-20:]:
            tag = "User" if m["role"] == "user" else "ONYX"
            content = m["content"][:500]
            lines.append(f"{tag}: {content}")
        lines.append(f"\n[New message]\nUser: {new_message}")
        return "\n".join(lines)

    async def _send_with_tools(self, message: str, on_tool_output=None,
                                max_rounds: int = 5) -> str:
        user_msg = UserMessage(text=message)
        response = await self.llm_chat.send_message(user_msg)

        for _ in range(max_rounds):
            calls = self.tool_service.parse_tool_calls(response)
            if not calls:
                break

            results = []
            for c in calls:
                result = self.tool_service.execute(c)
                results.append(f"[{c['type']}] {result}")
                if on_tool_output:
                    on_tool_output(c["type"], c.get("content", ""), result)

            followup = UserMessage(
                text=f"[Tool results]\n{''.join(results)}\n\nContinue based on these results."
            )
            response = await self.llm_chat.send_message(followup)

        return response
