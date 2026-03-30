"""
app/utils/logger.py - 日志工具
"""

import os
import logging
from datetime import datetime


LOG_DIR = os.path.expanduser("~/.env_manager/logs")
LOG_FILE = os.path.join(LOG_DIR, f"env_manager_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logger(name: str = "env_manager") -> logging.Logger:
    """设置日志"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # 文件 Handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        
        # 控制台 Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
