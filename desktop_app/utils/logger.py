"""Logging utility for ONYX application"""
import logging
import sys
from pathlib import Path
from datetime import datetime

_logger = None

def setup_logger(name: str = "onyx", level: int = logging.INFO) -> logging.Logger:
    """Setup and configure application logger"""
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Create logs directory
    log_dir = Path("Onyx/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler
    log_file = log_dir / f"onyx_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Get the application logger"""
    if _logger is None:
        return setup_logger()
    return _logger
