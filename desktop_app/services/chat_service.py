"""Chat service — Claude via official Anthropic SDK with tool support"""
import os
import anthropic
from dotenv import load_dotenv

from desktop_app.services.storage_service import StorageService
from desktop_app.services.tool_service import ToolService
from desktop_app.utils.logger import get_logger

load_dotenv()
logger = get_logger()

ANTHROPIC_MODELS = [
    # Claude 4.6
    ("Sonnet 4.6",           "claude-sonnet-4-6"),
    ("Opus 4.6",             "claude-opus-4-6"),
    # Claude 4.5
    ("Sonnet 4.5",           "claude-sonnet-4-5-20250514"),
    ("Opus 4.5",             "claude-opus-4-5-20250514"),
    ("Haiku 4.5",            "claude-haiku-4-5-20251001"),
    # Claude 4
    ("Sonnet 4",             "claude-sonnet-4-20250514"),
    ("Opus 4",               "claude-opus-4-20250514"),
    # Claude 3.5
    ("Sonnet 3.5 v2",        "claude-3-5-sonnet-20241022"),
    ("Sonnet 3.5",           "claude-3-5-sonnet-20240620"),
    ("Haiku 3.5",            "claude-3-5-haiku-20241022"),
    # Claude 3
    ("Opus 3",               "claude-3-opus-20240229"),
    ("Sonnet 3",             "claude-3-sonnet-20240229"),
    ("Haiku 3",              "claude-3-haiku-20240307"),
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
        self.model_name = model_cfg.get("name", "claude-sonnet-4-6")

        self._system_message = self._build_system_message()
        self._active_chat_id = None
        self._client = None
        if self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)

    def _build_system_message(self) -> str:
        base = self.storage.build_system_message()
        tools = self.tool_service.get_tools_prompt()
        return f"{base}\n{tools}"

    def set_model(self, model_name: str):
        self.model_name = model_name
        settings = self.storage.get_settings()
        settings.setdefault("model", {})["name"] = model_name
        self.storage.save_settings(settings)
        logger.info(f"Model changed to {model_name}")

    def switch_chat(self, chat_id: int):
        self._active_chat_id = chat_id
        self._system_message = self._build_system_message()

    def reload_config(self):
        self._system_message = self._build_system_message()
        logger.info("Config reloaded")

    async def send_message(self, message: str, chat_id: int,
                           on_tool_output=None) -> str:
        if not self._client:
            return "No API key configured. Add CLAUDE_API_KEY to .env and restart."

        if self._active_chat_id != chat_id:
            self.switch_chat(chat_id)

        # Build proper message list from history
        history = self.storage.get_chat_messages(chat_id)
        messages = self._build_messages(history, message)

        self.storage.add_message(chat_id, "user", message)

        response = await self._send_with_tools(messages, on_tool_output)

        clean = ToolService.strip_tool_tags(response)
        self.storage.add_message(chat_id, "assistant", clean)
        return clean

    def _build_messages(self, history, new_message: str) -> list:
        """Build Anthropic messages array from chat history."""
        messages = []
        for m in history[-20:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": new_message})
        return messages

    async def _send_with_tools(self, messages: list, on_tool_output=None,
                                max_rounds: int = 5) -> str:
        response = self._client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            system=self._system_message,
            messages=messages,
        )
        text = response.content[0].text

        for _ in range(max_rounds):
            calls = self.tool_service.parse_tool_calls(text)
            if not calls:
                break

            results = []
            for c in calls:
                result = self.tool_service.execute(c)
                results.append(f"[{c['type']}] {result}")
                if on_tool_output:
                    on_tool_output(c["type"], c.get("content", ""), result)

            messages.append({"role": "assistant", "content": text})
            messages.append({
                "role": "user",
                "content": "[Tool results]\n" + "\n\n".join(results) + "\n\nContinue based on these results.",
            })

            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=8192,
                system=self._system_message,
                messages=messages,
            )
            text = response.content[0].text

        return text
