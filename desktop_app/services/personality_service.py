"""Service for managing AI personality configuration"""
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()


class PersonalityService:
    def __init__(self):
        self.storage = StorageService()

    def get_personality(self) -> str:
        return self.storage.get_personality()

    def update_personality(self, content: str):
        self.storage.update_personality(content)
        logger.info("Personality updated")

    def get_knowledgebase(self) -> str:
        return self.storage.get_knowledgebase()

    def get_user_profile(self) -> str:
        return self.storage.get_user_profile()

    def get_instructions(self) -> str:
        return self.storage.get_instructions()

    def get_full_system_message(self) -> str:
        return self.storage.build_system_message()
