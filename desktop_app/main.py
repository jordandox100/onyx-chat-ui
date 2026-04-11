#!/usr/bin/env python3
import sys
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
from desktop_app.services.context_service import ContextService
from desktop_app.services.chat_service import ChatService
from desktop_app.services.letta_bridge import LettaBridge

# Load environment variables
load_dotenv()

def main():
    """Main entry point for ONYX desktop application"""
    logger = setup_logger()
    logger.info("Starting ONYX Application")

    # Initialize storage
    storage = StorageService()
    storage.initialize()

    # Initialize Supabase (optional — graceful fallback)
    supabase = SupabaseService()

    # Context service — replaces raw history replay with summaries
    context = ContextService(storage, supabase)

    # Chat service with context-aware message building
    chat_service = ChatService(storage=storage, context_service=context)

    # Bridge — connects UI to Letta/Supabase/chat
    bridge = LettaBridge(
        supabase=supabase,
        context_service=context,
        chat_service=chat_service,
    )

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow(bridge=bridge)
    window.show()

    logger.info("ONYX Application started successfully")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
