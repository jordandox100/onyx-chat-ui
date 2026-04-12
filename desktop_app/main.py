#!/usr/bin/env python3
"""ONYX entry point — auth, subscriptions, Supabase, Anthropic runtime."""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from desktop_app.utils.logger import setup_logger
from desktop_app.services.storage_service import StorageService
from desktop_app.services.supabase_service import SupabaseService
from desktop_app.services.runtime import OnyxRuntime
from desktop_app.services.chat_service import ChatService
from desktop_app.services.auth_service import AuthService
from desktop_app.services.shared_service import SharedService
from desktop_app.services.subscription_service import SubscriptionService
from desktop_app.ui.login_dialog import LoginDialog
from desktop_app.ui.main_window import MainWindow

load_dotenv()


def main():
    logger = setup_logger()
    logger.info("Starting ONYX")

    storage = StorageService()
    storage.initialize()

    supabase = SupabaseService()
    auth = AuthService(supabase=supabase)
    shared = SharedService(supabase=supabase)
    subs = SubscriptionService(supabase=supabase)
    runtime = OnyxRuntime(supabase=supabase, storage=storage)
    chat_service = ChatService(storage=storage, runtime=runtime)

    if supabase.available:
        auth.seed_admin()

    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    app.setStyle("Fusion")

    # Login
    if supabase.available:
        login = LoginDialog(auth)
        if login.exec() != LoginDialog.DialogCode.Accepted:
            sys.exit(0)
        username = auth.username
        is_admin = auth.is_admin
    else:
        username = "local"
        is_admin = False

    chat_service.set_admin(is_admin)
    chat_service.set_user(username, subs)

    window = MainWindow(
        runtime=runtime, chat_service=chat_service, supabase=supabase,
        auth=auth, shared=shared, subs=subs, username=username,
    )
    window.show()

    tier = subs.get_user_tier(username)
    logger.info(f"ONYX ready — user={username}, tier={tier}, admin={is_admin}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
