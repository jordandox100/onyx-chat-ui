"""Storage service — local SQLite mirror for UI display + app settings.

SQLite stores:
  - Chat/message mirror (for visible transcript display)
  - App settings (TTS config, model selection, theme)
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()

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
        self.base_path = Path(base_path).absolute()
        self.history_path = self.base_path / "history"
        self.config_path = self.base_path / "config"
        self.voice_path = self.base_path / "voice"
        self.logs_path = self.base_path / "logs"
        self.db_path = self.history_path / "chats.db"

    def initialize(self):
        """Initialize directories, settings, and database."""
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.voice_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        self._ensure_json("settings.json", DEFAULT_SETTINGS)
        self._init_database()
        logger.info(f"Storage initialized at: {self.base_path}")

    def _ensure_json(self, filename: str, default_data: dict):
        path = self.config_path / filename
        if not path.exists():
            path.write_text(json.dumps(default_data, indent=2))

    # ── Settings ──────────────────────────────────────────────

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

    # ── Database (UI display mirror only) ─────────────────────

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

    def get_messages_page(self, chat_id: int, offset: int = 0,
                          limit: int = 20) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE chat_id = ? "
            "ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages

    def get_message_count(self, chat_id: int) -> int:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
