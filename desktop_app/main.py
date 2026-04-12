#!/usr/bin/env python3
"""ONYX entry point — wires Letta runtime, Supabase state, and PySide6 UI.

Architecture:
  Letta = brain (memory, identity, compaction, tools, model)
  Supabase = app state mirror (tasks, events, files)
  SQLite = UI display mirror only (visible transcript)
  UI = interface, not intelligence
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from desktop_app.ui.main_window import MainWindow
from desktop_app.utils.logger import setup_logger
from desktop_app.services.storage_service import StorageService
from desktop_app.services.supabase_service import SupabaseService
from desktop_app.services.letta_bridge import LettaBridge
from desktop_app.services.chat_service import ChatService

load_dotenv()


def validate_config(logger):
    """Log startup config. Fail loudly if Letta is missing."""
    logger.info("=== ONYX Config ===")
    checks = {
        "LETTA_BASE_URL": ("REQUIRED", True),
        "LETTA_API_KEY": ("optional for self-hosted", False),
        "LETTA_AGENT_ID": ("optional, auto-creates", False),
        "SUPABASE_URL": ("optional", False),
        "SUPABASE_ANON_KEY": ("optional", False),
    }
    for var, (note, required) in checks.items():
        val = os.environ.get(var, "").strip()
        status = "SET" if val else "NOT SET"
        level = "WARNING" if required and not val else "INFO"
        logger.log(
            30 if level == "WARNING" else 20,
            f"  {var}: {status} ({note})"
        )


def main():
    logger = setup_logger()
    logger.info("Starting ONYX")
    validate_config(logger)

    # Local storage (UI display mirror + settings only)
    storage = StorageService()
    storage.initialize()

    # Supabase (optional app state)
    supabase = SupabaseService()

    # Letta bridge (the actual brain connection)
    bridge = LettaBridge(supabase=supabase)

    if bridge.available:
        health = bridge.health_check()
        if health["ok"]:
            logger.info("Letta health: OK")
            bridge.ensure_agent()
            logger.info(f"Letta agent: {bridge.status} — {bridge.status_detail}")
        else:
            logger.warning(f"Letta health failed: {health['detail']}")
    else:
        logger.warning(f"Letta: {bridge.status} — {bridge.status_detail}")

    # Chat service = thin relay (UI -> Letta -> mirror to SQLite)
    chat_service = ChatService(storage=storage, bridge=bridge)

    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    app.setStyle("Fusion")

    window = MainWindow(bridge=bridge, chat_service=chat_service)
    window.show()

    logger.info(
        f"ONYX ready — runtime={chat_service.runtime_name}, "
        f"letta={bridge.status}, supabase={supabase.status_text}"
    )
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
