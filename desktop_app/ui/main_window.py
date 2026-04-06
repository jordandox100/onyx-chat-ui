"""Main window for ONYX application"""
import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QInputDialog,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from desktop_app.ui.chat_widget import ChatWidget
from desktop_app.ui.styles import MAIN_STYLE
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.storage = StorageService()
        self.current_chat_id = None
        self.init_ui()
        self.load_chats()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ONYX - AI Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyleSheet(MAIN_STYLE)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)
        
        # Chat area
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        # Set initial sizes (sidebar: 300px, chat: rest)
        splitter.setSizes([300, 1100])
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
    def create_sidebar(self):
        """Create the sidebar with chat history"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(400)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # App title
        title = QLabel("ONYX")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #4a9eff;
            padding: 12px 8px;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("primaryButton")
        new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_btn.clicked.connect(self.new_chat)
        layout.addWidget(new_chat_btn)
        
        # Chat history label
        history_label = QLabel("Chat History")
        history_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #808080;
            padding: 12px 8px 4px 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(history_label)
        
        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_selected_chat)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_context_menu)
        layout.addWidget(self.chat_list)
        
        # Chat management buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_chat)
        btn_layout.addWidget(rename_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_chat)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        return sidebar
    
    def load_chats(self):
        """Load chat history from database"""
        self.chat_list.clear()
        chats = self.storage.get_all_chats()
        for chat in chats:
            self.chat_list.addItem(f"{chat['title']}")
            item = self.chat_list.item(self.chat_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, chat['id'])
    
    def new_chat(self):
        """Create a new chat"""
        chat_id = self.storage.create_chat("New Chat")
        self.current_chat_id = chat_id
        self.load_chats()
        self.chat_widget.clear_chat()
        self.chat_widget.set_chat_id(chat_id)
        logger.info(f"Created new chat: {chat_id}")
    
    def load_selected_chat(self, item):
        """Load selected chat from history"""
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_chat_id = chat_id
        messages = self.storage.get_chat_messages(chat_id)
        self.chat_widget.load_chat(chat_id, messages)
        logger.info(f"Loaded chat: {chat_id}")
    
    def rename_chat(self):
        """Rename selected chat"""
        current_item = self.chat_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a chat to rename.")
            return
        
        chat_id = current_item.data(Qt.ItemDataRole.UserRole)
        current_title = current_item.text()
        
        new_title, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new name:",
            text=current_title
        )
        
        if ok and new_title:
            self.storage.update_chat_title(chat_id, new_title)
            self.load_chats()
            logger.info(f"Renamed chat {chat_id} to: {new_title}")
    
    def delete_chat(self):
        """Delete selected chat"""
        current_item = self.chat_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a chat to delete.")
            return
        
        chat_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Delete Chat",
            "Are you sure you want to delete this chat?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.storage.delete_chat(chat_id)
            self.load_chats()
            if chat_id == self.current_chat_id:
                self.chat_widget.clear_chat()
                self.current_chat_id = None
            logger.info(f"Deleted chat: {chat_id}")
    
    def show_chat_context_menu(self, position):
        """Show context menu for chat list"""
        pass
