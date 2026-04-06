"""Chat service for AI conversation management"""
import os
from typing import List, Dict
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
        self.api_key = os.getenv("CLAUDE_API_KEY")
        
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not found in environment")
            self.api_key = "dummy_key"  # Placeholder for initial run
        
        # Load personality
        self.personality = self.storage.get_personality()
        
        # Initialize LLM chat with Claude Opus 4.6
        self.llm_chat = LlmChat(
            api_key=self.api_key,
            session_id="onyx_session",
            system_message=self.personality
        )
        # Set model to Claude Opus 4.6
        self.llm_chat.with_model("anthropic", "claude-opus-4-6")
        
        logger.info("Chat service initialized with Claude Opus 4.6")
    
    async def send_message(self, message: str, chat_id: int) -> str:
        """Send a message and get AI response"""
        try:
            # Save user message
            self.storage.add_message(chat_id, "user", message)
            
            # Get conversation history for context
            messages = self.storage.get_chat_messages(chat_id)
            
            # Create user message
            user_message = UserMessage(text=message)
            
            # Get AI response
            response = await self.llm_chat.send_message(user_message)
            
            # Save assistant response
            self.storage.add_message(chat_id, "assistant", response)
            
            logger.info(f"Chat {chat_id}: message sent and response received")
            return response
            
        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            logger.error(error_msg)
            return error_msg
