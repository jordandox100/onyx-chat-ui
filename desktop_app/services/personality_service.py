"""Service for managing AI personality configuration"""
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

class PersonalityService:
    def __init__(self):
        """Initialize personality service"""
        self.storage = StorageService()
    
    def get_personality(self) -> str:
        """Get current personality configuration"""
        return self.storage.get_personality()
    
    def update_personality(self, content: str):
        """Update personality configuration"""
        self.storage.update_personality(content)
        logger.info("Personality updated")
    
    def reset_to_default(self):
        """Reset personality to default"""
        default_personality = """You are ONYX, a helpful and intelligent AI assistant.

Your personality:
- Professional yet friendly and approachable
- Clear and concise in your responses
- Patient and understanding
- Knowledgeable across many topics
- Always honest when you don't know something
- Respectful and considerate of the user

Your goal is to assist users with their questions and tasks in the most helpful way possible.
"""
        self.update_personality(default_personality)
