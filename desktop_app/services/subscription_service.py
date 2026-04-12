"""Subscription service — tiers, limits, tokens, Square payments.

Tiers:
  free    — 5 messages/day, no tools
  pro     — $19.99/mo, unlimited messages, memory tools only
  builder — $34.99/mo, all tools, 500 build tokens/mo, can buy more

Token top-ups (builder only):
  $20 = 200 tokens
  $35 = 400 tokens
  $50 = 700 tokens
  $100 = 1600 tokens

Square Checkout creates a payment link → user pays in browser → we verify.
"""
import os
import uuid
import webbrowser
from datetime import datetime, timezone
from typing import Optional, Dict

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    from square import Square
    SQUARE_AVAILABLE = True
except ImportError:
    SQUARE_AVAILABLE = False
    Square = None

# ── Tier Config ───────────────────────────────────────────────

TIERS = {
    "free": {
        "name": "Free",
        "price_cents": 0,
        "daily_messages": 5,
        "tools": [],
        "monthly_tokens": 0,
    },
    "pro": {
        "name": "Pro",
        "price_cents": 1999,
        "daily_messages": -1,  # unlimited
        "tools": ["memory_search"],
        "monthly_tokens": 0,
    },
    "builder": {
        "name": "Builder",
        "price_cents": 3499,
        "daily_messages": -1,  # unlimited
        "tools": ["memory_search", "web_search", "file_read", "file_write",
                  "file_search", "shell_exec"],
        "monthly_tokens": 500,
    },
}

TOKEN_PACKS = [
    {"label": "200 tokens",  "tokens": 200,  "price_cents": 2000, "price_display": "$20"},
    {"label": "400 tokens",  "tokens": 400,  "price_cents": 3500, "price_display": "$35"},
    {"label": "700 tokens",  "tokens": 700,  "price_cents": 5000, "price_display": "$50"},
    {"label": "1600 tokens", "tokens": 1600, "price_cents": 10000, "price_display": "$100"},
]


class SubscriptionService:
    def __init__(self, supabase=None):
        self.supabase = supabase
        self._square = None
        self._location_id = ""
        self._connect_square()

    def _connect_square(self):
        if not SQUARE_AVAILABLE:
            logger.info("Square SDK not installed")
            return
        token = os.environ.get("SQUARE_ACCESS_TOKEN", "").strip()
        self._location_id = os.environ.get("SQUARE_LOCATION_ID", "").strip()
        if not token:
            logger.info("SQUARE_ACCESS_TOKEN not set")
            return
        env = os.environ.get("SQUARE_ENVIRONMENT", "sandbox")
        self._square = Square(token=token, environment=env)
        logger.info(f"Square connected ({env})")

    @property
    def square_available(self) -> bool:
        return self._square is not None

    # ── Subscription CRUD ─────────────────────────────────────

    def get_user_tier(self, username: str) -> str:
        """Get user's current subscription tier."""
        if not self.supabase or not self.supabase.available:
            return "free"
        try:
            result = (self.supabase._client.table("subscriptions")
                      .select("*").eq("username", username)
                      .eq("active", True).single().execute())
            if result.data:
                return result.data.get("tier", "free")
        except Exception:
            pass
        return "free"

    def get_subscription(self, username: str) -> Optional[Dict]:
        if not self.supabase or not self.supabase.available:
            return None
        try:
            result = (self.supabase._client.table("subscriptions")
                      .select("*").eq("username", username)
                      .eq("active", True).single().execute())
            return result.data
        except Exception:
            return None

    def set_subscription(self, username: str, tier: str) -> bool:
        """Admin: set a user's subscription tier."""
        if not self.supabase or not self.supabase.available:
            return False
        try:
            # Deactivate old
            self.supabase._client.table("subscriptions").update(
                {"active": False}
            ).eq("username", username).eq("active", True).execute()

            if tier == "free":
                return True

            # Create new
            tokens = TIERS.get(tier, {}).get("monthly_tokens", 0)
            self.supabase._client.table("subscriptions").insert({
                "username": username,
                "tier": tier,
                "active": True,
                "token_balance": tokens,
            }).execute()
            logger.info(f"Subscription set: {username} -> {tier}")
            return True
        except Exception as e:
            logger.error(f"set_subscription: {e}")
            return False

    def cancel_subscription(self, username: str) -> bool:
        return self.set_subscription(username, "free")

    # ── Message Limits ────────────────────────────────────────

    def get_daily_message_count(self, username: str) -> int:
        """Count messages sent today."""
        if not self.supabase or not self.supabase.available:
            return 0
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            result = (self.supabase._client.table("message_usage")
                      .select("count", count="exact")
                      .eq("username", username).gte("date", today).execute())
            return result.count or 0
        except Exception:
            return 0

    def record_message(self, username: str):
        """Record a message use."""
        if not self.supabase or not self.supabase.available:
            return
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self.supabase._client.table("message_usage").insert({
                "username": username, "date": today,
            }).execute()
        except Exception as e:
            logger.error(f"record_message: {e}")

    def can_send_message(self, username: str) -> tuple[bool, str]:
        """Check if user can send a message. Returns (allowed, reason)."""
        tier = self.get_user_tier(username)
        limit = TIERS.get(tier, TIERS["free"])["daily_messages"]
        if limit == -1:
            return True, ""
        used = self.get_daily_message_count(username)
        if used >= limit:
            return False, f"Daily message limit reached ({limit}). Upgrade to Pro for unlimited."
        return True, ""

    # ── Tokens ────────────────────────────────────────────────

    def get_token_balance(self, username: str) -> int:
        sub = self.get_subscription(username)
        if sub:
            return sub.get("token_balance", 0)
        return 0

    def use_token(self, username: str, amount: int = 1) -> bool:
        """Deduct tokens. Returns True if sufficient."""
        sub = self.get_subscription(username)
        if not sub:
            return False
        balance = sub.get("token_balance", 0)
        if balance < amount:
            return False
        try:
            self.supabase._client.table("subscriptions").update({
                "token_balance": balance - amount,
            }).eq("username", username).eq("active", True).execute()
            return True
        except Exception as e:
            logger.error(f"use_token: {e}")
            return False

    def add_tokens(self, username: str, amount: int) -> bool:
        sub = self.get_subscription(username)
        if not sub:
            return False
        balance = sub.get("token_balance", 0)
        try:
            self.supabase._client.table("subscriptions").update({
                "token_balance": balance + amount,
            }).eq("username", username).eq("active", True).execute()
            return True
        except Exception as e:
            logger.error(f"add_tokens: {e}")
            return False

    # ── Tool Access ───────────────────────────────────────────

    def get_allowed_tools(self, username: str) -> list:
        tier = self.get_user_tier(username)
        return list(TIERS.get(tier, TIERS["free"])["tools"])

    def can_use_tool(self, username: str, tool_name: str) -> bool:
        allowed = self.get_allowed_tools(username)
        return tool_name in allowed

    # ── Square Payments ───────────────────────────────────────

    def create_checkout_link(self, username: str, tier: str = None,
                             token_pack_idx: int = None) -> Optional[str]:
        """Create a Square payment link. Opens in browser. Returns URL."""
        if not self._square or not self._location_id:
            logger.warning("Square not configured")
            return None

        if tier:
            cfg = TIERS.get(tier)
            if not cfg or cfg["price_cents"] == 0:
                return None
            name = f"ONYX {cfg['name']} Subscription"
            amount = cfg["price_cents"]
            note = f"subscription:{tier}:{username}"
        elif token_pack_idx is not None:
            if token_pack_idx < 0 or token_pack_idx >= len(TOKEN_PACKS):
                return None
            pack = TOKEN_PACKS[token_pack_idx]
            name = f"ONYX {pack['label']}"
            amount = pack["price_cents"]
            note = f"tokens:{pack['tokens']}:{username}"
        else:
            return None

        try:
            result = self._square.checkout.payment_links.create(
                idempotency_key=str(uuid.uuid4()),
                quick_pay={
                    "name": name,
                    "price_money": {
                        "amount": amount,
                        "currency": "USD",
                    },
                    "location_id": self._location_id,
                },
                payment_note=note,
            )
            url = result.payment_link.url
            logger.info(f"Payment link created: {url}")
            webbrowser.open(url)
            return url
        except Exception as e:
            logger.error(f"Square checkout error: {e}")
            return None
