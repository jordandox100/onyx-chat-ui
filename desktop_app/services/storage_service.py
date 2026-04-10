"""Storage service for managing local data and chat history"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()

DEFAULT_PERSONALITY = """You are ONYX, a powerful local AI assistant running on the user's Linux desktop.

Your personality:
- Sharp, direct, and efficient — you don't waste words
- Technically savvy — comfortable with code, system admin, and power-user topics
- Friendly but not bubbly — more like a trusted colleague than a customer service bot
- You remember context from the conversation and build on it
- You're honest when you don't know something and say so plainly
- You adapt your tone to the user — casual if they're casual, precise if they need precision

Your goal is to be genuinely useful. Solve the actual problem, not the surface question.
"""

DEFAULT_KNOWLEDGEBASE = """# ONYX Knowledgebase
# Add facts, reference material, or context you want ONYX to always know.
# Everything in this file is included in ONYX's context for every conversation.
#
# Examples:
#   My home server runs Ubuntu 22.04 with 32GB RAM
#   The project uses Python 3.12, FastAPI, and PostgreSQL
#   Our team standup is at 9am EST Monday–Friday
#   API docs are at https://internal.example.com/docs
#
# Lines starting with # are comments and will be ignored.
"""

DEFAULT_USER_PROFILE = """# User Profile
# Tell ONYX who you are. This is included in every conversation
# so the assistant can personalise responses.
#
# Name:
#   (your name here)
#
# Role / Occupation:
#   (e.g. software engineer, student, sysadmin)
#
# Location / Timezone:
#   (e.g. EST, Berlin, UTC+9)
#
# Preferred Language:
#   English
#
# Technical Level:
#   (beginner / intermediate / advanced)
#
# Anything else ONYX should know about you:
#   (hobbies, projects you're working on, communication preferences, etc.)
"""

DEFAULT_INSTRUCTIONS = """# Custom Instructions
# Rules and guidelines that ONYX must follow in every response.
# These override default behaviour when they conflict.
#
# Examples:
#   Always respond in British English
#   When writing code, use type hints and docstrings
#   Keep responses under 200 words unless I ask for detail
#   Never suggest proprietary software — prefer open source
#   Format lists with dashes, not bullets
#   If I ask about my server, assume Ubuntu 22.04 unless I say otherwise
#
# Lines starting with # are comments and will be ignored.
"""

DEFAULT_SETTINGS = {
    "tts": {
        "enabled": False,
        "rate": 175,
        "volume": 0.9,
    },
    "voice_input": {
        "record_seconds": 5,
    },
    "model": {
        "provider": "anthropic",
        "name": "claude-sonnet-4-6",
    },
    "theme": "dark",
}


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
        """Initialize directory structure, config files, and database"""
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.voice_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Create default config files if they don't exist
        self._ensure_file("personality.txt", DEFAULT_PERSONALITY)
        self._ensure_file("knowledgebase.txt", DEFAULT_KNOWLEDGEBASE)
        self._ensure_file("user.txt", DEFAULT_USER_PROFILE)
        self._ensure_file("instructions.txt", DEFAULT_INSTRUCTIONS)
        self._ensure_json("settings.json", DEFAULT_SETTINGS)

        self._init_database()
        logger.info(f"Storage initialized at: {self.base_path}")

    def _ensure_file(self, filename: str, default_content: str):
        path = self.config_path / filename
        if not path.exists():
            path.write_text(default_content)
            logger.info(f"Created default {filename}")

    def _ensure_json(self, filename: str, default_data: dict):
        path = self.config_path / filename
        if not path.exists():
            path.write_text(json.dumps(default_data, indent=2))
            logger.info(f"Created default {filename}")

    # ── Config file accessors ─────────────────────────────────

    def _read_config_text(self, filename: str, fallback: str = "") -> str:
        """Read a text config file, stripping comment lines."""
        path = self.config_path / filename
        if not path.exists():
            return fallback
        lines = path.read_text().splitlines()
        content = "\n".join(l for l in lines if not l.strip().startswith("#"))
        return content.strip()

    def _read_config_raw(self, filename: str, fallback: str = "") -> str:
        """Read full file content including comments."""
        path = self.config_path / filename
        if not path.exists():
            return fallback
        return path.read_text()

    def get_personality(self) -> str:
        return self._read_config_raw("personality.txt", DEFAULT_PERSONALITY)

    def update_personality(self, content: str):
        (self.config_path / "personality.txt").write_text(content)
        logger.info("Updated personality file")

    def get_knowledgebase(self) -> str:
        return self._read_config_text("knowledgebase.txt")

    def get_user_profile(self) -> str:
        return self._read_config_text("user.txt")

    def get_instructions(self) -> str:
        return self._read_config_text("instructions.txt")

    def get_settings(self) -> dict:
        path = self.config_path / "settings.json"
        if not path.exists():
            return dict(DEFAULT_SETTINGS)
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt settings.json — using defaults")
            return dict(DEFAULT_SETTINGS)

    def save_settings(self, data: dict):
        path = self.config_path / "settings.json"
        path.write_text(json.dumps(data, indent=2))
        logger.info("Saved settings")

    def build_system_message(self) -> str:
        """Assemble the full system prompt from all config files."""
        parts = [self.get_personality()]

        kb = self.get_knowledgebase()
        if kb:
            parts.append(f"\n--- Knowledgebase ---\n{kb}")

        user = self.get_user_profile()
        if user:
            parts.append(f"\n--- About the User ---\n{user}")

        instr = self.get_instructions()
        if instr:
            parts.append(f"\n--- Custom Instructions ---\n{instr}")

        return "\n".join(parts)

    # ── Database ──────────────────────────────────────────────

    def _init_database(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (title) VALUES (?)", (title,))
        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Created chat {chat_id}: {title}")
        return chat_id

    def get_all_chats(self) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chats ORDER BY updated_at DESC")
        chats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return chats

    def get_chat(self, chat_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
        chat = cursor.fetchone()
        conn.close()
        return dict(chat) if chat else None

    def update_chat_title(self, chat_id: int, title: str):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, chat_id),
        )
        conn.commit()
        conn.close()
        logger.info(f"Updated chat {chat_id} title: {title}")

    def delete_chat(self, chat_id: int):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted chat {chat_id}")

    def add_message(self, chat_id: int, role: str, content: str):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        cursor.execute(
            "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chat_id,),
        )
        conn.commit()
        conn.close()

    def get_chat_messages(self, chat_id: int) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
            (chat_id,),
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages
