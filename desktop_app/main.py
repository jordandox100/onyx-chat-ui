#!/usr/bin/env python3
"""ONYX entry point — Supabase + Anthropic runtime, PySide6 UI.

No Letta. No hidden overhead.
Runtime = direct Anthropic calls with compact Supabase-backed state.
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
from desktop_app.services.runtime import OnyxRuntime
from desktop_app.services.chat_service import ChatService

load_dotenv()


def validate_config(logger):
    logger.info("=== ONYX Config ===")
    for var, note in [
        ("ANTHROPIC_API_KEY", "REQUIRED — model calls"),
        ("SUPABASE_URL", "persistent memory/state"),
        ("SUPABASE_ANON_KEY", "persistent memory/state"),
    ]:
        val = os.environ.get(var, "").strip()
        logger.info(f"  {var}: {'SET' if val else 'NOT SET'} ({note})")


def main():
    logger = setup_logger()
    logger.info("Starting ONYX")
    validate_config(logger)

    storage = StorageService()
    storage.initialize()

    supabase = SupabaseService()
    runtime = OnyxRuntime(supabase=supabase)
    chat_service = ChatService(storage=storage, runtime=runtime)

    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    app.setStyle("Fusion")

    window = MainWindow(runtime=runtime, chat_service=chat_service, supabase=supabase)
    window.show()

    logger.info(
        f"ONYX ready — runtime={chat_service.runtime_name}, "
        f"supabase={supabase.status_text}"
    )
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
