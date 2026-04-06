#!/usr/bin/env python3
import sys
import os
import asyncio
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from desktop_app.ui.main_window import MainWindow
from desktop_app.utils.logger import setup_logger
from desktop_app.services.storage_service import StorageService

# Load environment variables
load_dotenv()

def main():
    """Main entry point for ONYX desktop application"""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting ONYX Application")
    
    # Initialize storage structure
    storage = StorageService()
    storage.initialize()
    
    # Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ONYX")
    app.setOrganizationName("ONYX")
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("ONYX Application started successfully")
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
