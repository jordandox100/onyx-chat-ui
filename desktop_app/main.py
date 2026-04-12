#!/usr/bin/env python3
"""ONYX entry point — wires Letta runtime, Supabase state, and PySide6 UI."""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from desktop_app.ui.main_window import MainWindow
from desktop_app.utils.logger import setup_logger
from desktop_app.services.storage_service import StorageService
from desktop_app.services.supabase_service import SupabaseService
from desktop_app.services.letta_bridge import LettaBridge
from desktop_app.services.chat_service import ChatService

# Load environment variables
load_dotenv()


def validate_config(logger):
    """Log startup config status for each service."""
    logger.info("=== ONYX Config Validation ===")

    letta_url = os.environ.get("LETTA_BASE_URL", "").strip()
    letta_key = os.environ.get("LETTA_API_KEY", "").strip()
    letta_agent = os.environ.get("LETTA_AGENT_ID", "").strip()
    supa_url = os.environ.get("SUPABASE_URL", "").strip()
    supa_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()

    logger.info(f"  LETTA_BASE_URL:  {'SET' if letta_url else 'NOT SET'}")
    logger.info(f"  LETTA_API_KEY:   {'SET' if letta_key else 'NOT SET (ok for self-hosted)'}")
    logger.info(f"  LETTA_AGENT_ID:  {'SET' if letta_agent else 'NOT SET (will auto-create)'}")
    logger.info(f"  SUPABASE_URL:    {'SET' if supa_url else 'NOT SET (optional)'}")
    logger.info(f"  SUPABASE_ANON_KEY: {'SET' if supa_key else 'NOT SET (optional)'}")

    if not letta_url:
        logger.warning(
            "LETTA_BASE_URL not set. ONYX will show setup instructions. "
            "Run: docker run -d -p 8283:8283 lettaai/letta:latest"
        )


def main():
    """Main entry point for ONYX desktop application."""
    logger = setup_logger()
    logger.info("Starting ONYX Application")

    # Validate config
    validate_config(logger)

    # Initialize local storage
    storage = StorageService()
    storage.initialize()

    # Initialize Supabase (optional — graceful fallback)
    supabase = SupabaseService()

    # Initialize Letta bridge (primary runtime)
    bridge = LettaBridge(supabase=supabase, storage=storage)

    # Letta health check
    if bridge.available:
        health = bridge.health_check()
        if health["ok"]:
            logger.info(f"Letta health: OK")
            # Ensure ONYX agent exists
            bridge.ensure_agent()
            logger.info(f"Letta agent: {bridge.status} — {bridge.status_detail}")
        else:
            logger.warning(f"Letta health check failed: {health['detail']}")
    else:
        logger.info(f"Letta status: {bridge.status} — {bridge.status_detail}")

    # Chat service routes through Letta bridge
    chat_service = ChatService(storage=storage, bridge=bridge)

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow(bridge=bridge, chat_service=chat_service)
    window.show()

    logger.info(
        f"ONYX started — runtime={chat_service.runtime_name}, "
        f"letta={bridge.status}, supabase={supabase.status_text}"
    )

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
