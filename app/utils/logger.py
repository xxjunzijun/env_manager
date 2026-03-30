"""
app/utils/logger.py - 日志工具

统一的日志模块，支持：
- 文件日志（DEBUG 级别）
- 控制台日志（INFO 级别）
- Windows 安全字符处理
- 自动创建日志目录
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 日志目录 (项目相对路径)
LOG_DIR = PROJECT_ROOT / ".env_manager" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"env_manager_{datetime.now().strftime('%Y%m%d')}.log"


class SafeStreamHandler(logging.StreamHandler):
    """安全的控制台 Handler，处理 Windows 编码问题"""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            # Windows 控制台只支持部分 Unicode，替换特殊字符
            if sys.platform == 'win32':
                replacements = {
                    '●': '[*]', '✅': '[OK]', '❌': '[X]', '⚠️': '[!]',
                    '📍': '[]', '🖥️': '[SVR]', '🔌': '[SW]', '💾': '[MEM]',
                    '📊': '[STAT]', '📈': '[LOAD]', '⏱️': '[TIME]', '🏷️': '[TAG]',
                    '🚪': '[GW]', '🔗': '[LINK]', '📡': '[DNS]', '⚙️': '[KERNEL]',
                    '➕': '[+]', '➖': '[-]', '📝': '[EDIT]', '🔍': '[SEARCH]',
                    '💾': '[DISK]', '📋': '[INFO]', '🗂️': '[FOLDER]',
                    '⏰': '[CLOCK]', '🔄': '[SYNC]', '❗': '[!]', '✓': '[OK]',
                }
                for old, new in replacements.items():
                    msg = msg.replace(old, new)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logger(name: str = "env_manager") -> logging.Logger:
    """设置日志
    
    Args:
        name: Logger 名称
        
    Returns:
        配置好的 Logger 实例
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # 文件 Handler - 记录所有级别
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        
        # 控制台 Handler - 只记录 INFO 及以上
        console_handler = SafeStreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """获取 Logger 的便捷方法
    
    Args:
        name: 如果提供，返回名为 name 的子 Logger
              否则返回根 Logger
        
    Returns:
        Logger 实例
    """
    if name:
        return logging.getLogger(f"env_manager.{name}")
    return logging.getLogger("env_manager")
