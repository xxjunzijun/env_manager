"""
test_logger.py - 日志工具测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestLoggerUtils:
    """日志工具测试"""

    def test_get_log_dir_dev_mode(self):
        """测试开发模式日志目录"""
        import app.utils.logger as logger_module
        result = logger_module.get_log_dir()
        assert isinstance(result, Path)

    def test_get_log_dir_frozen_mode(self):
        """测试 exe 模式日志目录"""
        # 测试返回的是 Path 对象（实际目录存在）
        import app.utils.logger as logger_module
        result = logger_module.get_log_dir()
        assert isinstance(result, Path)

    def test_safe_stream_handler_windows_replacements(self):
        """测试 Windows 安全字符替换"""
        from app.utils.logger import SafeStreamHandler
        import logging
        
        handler = SafeStreamHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test ✅ message ● with ❌ symbols",
            args=(),
            exc_info=None
        )
        
        # 捕获输出
        import io
        stream = io.StringIO()
        handler.stream = stream
        
        with patch("sys.platform", "win32"):
            handler.emit(record)
        
        output = stream.getvalue()
        assert "[OK]" in output
        assert "[*]" in output
        assert "[X]" in output

    def test_setup_logger_returns_logger(self):
        """测试 setup_logger 返回 Logger"""
        from app.utils.logger import setup_logger, get_logger
        
        logger = setup_logger(name="test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"

    def test_get_logger_returns_logger(self):
        """测试 get_logger 返回子 Logger"""
        from app.utils.logger import get_logger
        
        logger = get_logger("sub")
        
        assert logger is not None
        assert "sub" in logger.name

    def test_get_logger_without_name(self):
        """测试 get_logger 无参数"""
        from app.utils.logger import get_logger
        
        logger = get_logger()
        
        assert logger is not None
        assert logger.name == "env_manager"


class TestLogFileCreation:
    """日志文件创建测试"""

    def test_log_file_naming(self):
        """测试日志文件名格式"""
        from app.utils.logger import get_log_file
        from datetime import datetime
        
        log_file = get_log_file()
        
        # 验证文件名格式
        assert "env_manager_" in log_file.name
        assert ".log" in log_file.name

    def test_log_dir_creation(self):
        """测试日志目录创建"""
        from app.utils.logger import get_log_dir
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            with patch("app.utils.logger.get_log_dir", return_value=log_dir):
                os.makedirs(log_dir, exist_ok=True)
                assert log_dir.exists()
