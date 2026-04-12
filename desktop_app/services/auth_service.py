"""Auth service — user login/register with Supabase users table + bcrypt."""
import bcrypt
from typing import Optional, Dict

from desktop_app.utils.logger import get_logger

logger = get_logger()

ADMIN_USERNAME = "onyxadmin"
ADMIN_PASSWORD = "Gem266726!"


class AuthService:
    """Handles user auth against Supabase users table."""

    def __init__(self, supabase=None):
        self.supabase = supabase
        self._current_user = None

    @property
    def current_user(self) -> Optional[Dict]:
        return self._current_user

    @property
    def is_admin(self) -> bool:
        return bool(self._current_user and self._current_user.get("is_admin"))

    @property
    def username(self) -> str:
        return (self._current_user or {}).get("username", "")

    def seed_admin(self):
        """Create admin account if it doesn't exist."""
        if not self.supabase or not self.supabase.available:
            logger.warning("Cannot seed admin — Supabase not available")
            return
        existing = self._get_user(ADMIN_USERNAME)
        if existing:
            logger.info("Admin account exists")
            return
        pw_hash = bcrypt.hashpw(
            ADMIN_PASSWORD.encode(), bcrypt.gensalt()
        ).decode()
        try:
            self.supabase._client.table("users").insert({
                "username": ADMIN_USERNAME,
                "password_hash": pw_hash,
                "is_admin": True,
            }).execute()
            logger.info("Admin account seeded")
        except Exception as e:
            logger.error(f"Admin seed failed: {e}")

    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Register a new user. Returns (success, message)."""
        if not self.supabase or not self.supabase.available:
            return False, "Supabase not configured"
        if not username or not password:
            return False, "Username and password required"
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        existing = self._get_user(username)
        if existing:
            return False, "Username already taken"

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            self.supabase._client.table("users").insert({
                "username": username,
                "password_hash": pw_hash,
                "is_admin": False,
            }).execute()
            logger.info(f"Registered user: {username}")
            return True, "Account created"
        except Exception as e:
            logger.error(f"Register failed: {e}")
            return False, str(e)

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Login. Returns (success, message)."""
        if not self.supabase or not self.supabase.available:
            return False, "Supabase not configured"
        user = self._get_user(username)
        if not user:
            return False, "Invalid username or password"
        stored_hash = user.get("password_hash", "")
        if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return False, "Invalid username or password"
        self._current_user = {
            "id": user.get("id"),
            "username": user.get("username"),
            "is_admin": user.get("is_admin", False),
        }
        logger.info(f"Logged in: {username} (admin={self.is_admin})")
        return True, "Login successful"

    def logout(self):
        self._current_user = None

    def get_all_users(self) -> list:
        """Admin only: list all users."""
        if not self.is_admin:
            return []
        if not self.supabase or not self.supabase.available:
            return []
        try:
            result = (self.supabase._client.table("users")
                      .select("id,username,is_admin,created_at")
                      .order("created_at").execute())
            return result.data or []
        except Exception as e:
            logger.error(f"get_all_users: {e}")
            return []

    def _get_user(self, username: str) -> Optional[Dict]:
        if not self.supabase or not self.supabase.available:
            return None
        try:
            result = (self.supabase._client.table("users")
                      .select("*").eq("username", username)
                      .single().execute())
            return result.data
        except Exception:
            return None
