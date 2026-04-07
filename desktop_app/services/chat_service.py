"""Chat service for AI conversation management using Claude Opus 4.6"""
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv

from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

load_dotenv()
logger = get_logger()


class ChatService:
    def __init__(self):
        """Initialize chat service with Claude Opus 4.6"""
        self.storage = StorageService()
        self.api_key = os.getenv("CLAUDE_API_KEY", "").strip()

        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not set in .env — AI chat will not work until a key is provided.")

        self.personality = self.storage.get_personality()

        self.llm_chat = LlmChat(
            api_key=self.api_key,
            session_id="onyx_session",
            system_message=self.personality
        )
        self.llm_chat.with_model("anthropic", "claude-opus-4-6")
        logger.info("Chat service initialized with Claude Opus 4.6")

    async def send_message(self, message: str, chat_id: int) -> str:
        """Send a message and get AI response"""
        if not self.api_key:
            return "No API key configured. Please add your CLAUDE_API_KEY to the .env file."

        try:
            self.storage.add_message(chat_id, "user", message)
            user_message = UserMessage(text=message)
            response = await self.llm_chat.send_message(user_message)
            self.storage.add_message(chat_id, "assistant", response)
            logger.info(f"Chat {chat_id}: message sent and response received")
            return response

        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            logger.error(error_msg)
            return error_msg
