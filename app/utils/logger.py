"""
app/utils/logger.py - 日志工具

统一的日志模块，支持：
- 文件日志（DEBUG 级别）
- 控制台日志（INFO 级别）
- Windows 安全字符处理
- 自动创建日志目录
- exe 模式下日志保存在 exe 同目录的 log 文件夹
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime


def get_log_dir() -> Path:
    """获取日志目录
    
    Returns:
        日志目录路径
    """
    # 检测是否打包为 exe（PyInstaller）
    if getattr(sys, 'frozen', False):
        # exe 模式：日志放在 exe 同目录的 log 文件夹
        exe_dir = Path(sys.executable).parent
        log_dir = exe_dir / "log"
    else:
        # 开发模式：日志放在项目根目录的 .env_manager/logs
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        log_dir = PROJECT_ROOT / ".env_manager" / "logs"
    
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_log_file() -> Path:
    """获取日志文件路径"""
    log_dir = get_log_dir()
    return log_dir / f"env_manager_{datetime.now().strftime('%Y%m%d')}.log"


# 日志配置
LOG_DIR = get_log_dir()
LOG_FILE = get_log_file()


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


def setup_logger(name: str = "env_manager", show_error_dialog: bool = True) -> logging.Logger:
    """设置日志
    
    Args:
        name: Logger 名称
        show_error_dialog: 是否显示错误弹窗（仅在非开发模式下启用）
        
    Returns:
        配置好的 Logger 实例
    """
    global LOG_DIR, LOG_FILE
    LOG_DIR = get_log_dir()
    LOG_FILE = get_log_file()
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
        
        # 记录日志路径
        logger.info(f"日志目录: {LOG_DIR}")
        logger.info(f"日志文件: {LOG_FILE}")
    
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
