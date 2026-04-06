"""Storage service for managing local data and chat history"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()

class StorageService:
    def __init__(self, base_path: str = "Onyx"):
        """Initialize storage service with base directory"""
        self.base_path = Path(base_path).absolute()
        self.history_path = self.base_path / "history"
        self.config_path = self.base_path / "config"
        self.voice_path = self.base_path / "voice"
        self.logs_path = self.base_path / "logs"
        self.db_path = self.history_path / "chats.db"
        
    def initialize(self):
        """Initialize directory structure and database"""
        # Create directories
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.voice_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Create personality file if it doesn't exist
        personality_file = self.config_path / "personality.txt"
        if not personality_file.exists():
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
            personality_file.write_text(default_personality)
            logger.info("Created default personality file")
        
        # Initialize database
        self._init_database()
        logger.info(f"Storage initialized at: {self.base_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def create_chat(self, title: str) -> int:
        """Create a new chat and return its ID"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chats (title) VALUES (?)",
            (title,)
        )
        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Created chat {chat_id}: {title}")
        return chat_id
    
    def get_all_chats(self) -> List[Dict]:
        """Get all chats ordered by most recent"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chats ORDER BY updated_at DESC"
        )
        chats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return chats
    
    def get_chat(self, chat_id: int) -> Optional[Dict]:
        """Get a specific chat by ID"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chats WHERE id = ?",
            (chat_id,)
        )
        chat = cursor.fetchone()
        conn.close()
        return dict(chat) if chat else None
    
    def update_chat_title(self, chat_id: int, title: str):
        """Update chat title"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, chat_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"Updated chat {chat_id} title: {title}")
    
    def delete_chat(self, chat_id: int):
        """Delete a chat and all its messages"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted chat {chat_id}")
    
    def add_message(self, chat_id: int, role: str, content: str):
        """Add a message to a chat"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content)
        )
        # Update chat's updated_at timestamp
        cursor.execute(
            "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chat_id,)
        )
        conn.commit()
        conn.close()
    
    def get_chat_messages(self, chat_id: int) -> List[Dict]:
        """Get all messages for a chat"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages
    
    def get_personality(self) -> str:
        """Load personality text from config"""
        personality_file = self.config_path / "personality.txt"
        if personality_file.exists():
            return personality_file.read_text()
        return "You are ONYX, a helpful AI assistant."
    
    def update_personality(self, content: str):
        """Update personality file"""
        personality_file = self.config_path / "personality.txt"
        personality_file.write_text(content)
        logger.info("Updated personality file")
