"""
test_ssh_manager.py - SSH 管理器测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.core.ssh_manager import SSHConnection, SSHManager


class TestSSHConnection:
    """SSHConnection 测试"""

    def test_connection_creation(self):
        """测试连接创建"""
        mock_client = Mock()
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        
        assert conn.host == "192.168.1.1"
        assert conn.port == 22
        assert conn.is_connected == True
        assert conn.client is mock_client

    def test_execute_success(self):
        """测试命令执行成功"""
        mock_client = Mock()
        mock_stdout = Mock()
        mock_stdout.read.return_value = b"output content"
        mock_stdout.channel.recv_exit_status.return_value = 0
        
        mock_stderr = Mock()
        mock_stderr.read.return_value = b""
        
        mock_client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)
        
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        stdout, stderr, code = conn.execute("ls -la")
        
        assert stdout == "output content"
        assert stderr == ""
        assert code == 0

    def test_execute_failure(self):
        """测试命令执行失败"""
        mock_client = Mock()
        mock_stdout = Mock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        
        mock_stderr = Mock()
        mock_stderr.read.return_value = b"error message"
        
        mock_client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)
        
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        stdout, stderr, code = conn.execute("invalid_command")
        
        assert code == 1
        assert "error message" in stderr

    def test_execute_disconnected(self):
        """测试连接断开时的执行"""
        mock_client = Mock()
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        conn.is_connected = False
        
        stdout, stderr, code = conn.execute("ls")
        
        assert stdout == ""
        assert "Not connected" in stderr
        assert code == 1

    def test_execute_exception(self):
        """测试执行异常"""
        mock_client = Mock()
        mock_client.exec_command.side_effect = Exception("Connection reset")
        
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        stdout, stderr, code = conn.execute("ls")
        
        assert stdout == ""
        assert "Connection reset" in stderr
        assert code == 1

    def test_close(self):
        """测试关闭连接"""
        mock_client = Mock()
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        
        conn.close()
        
        assert conn.is_connected == False
        mock_client.close.assert_called_once()

    def test_close_already_closed(self):
        """测试关闭已关闭的连接"""
        mock_client = Mock()
        conn = SSHConnection(mock_client, "192.168.1.1", 22)
        conn.is_connected = False
        
        conn.close()
        mock_client.close.assert_not_called()


class TestSSHManager:
    """SSHManager 测试"""

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_connect_with_password(self, mock_ssh_client_class):
        """测试密码认证连接"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        manager = SSHManager(max_connections=5)
        conn = manager.connect(
            host="192.168.1.1",
            port=22,
            username="admin",
            password="secret"
        )
        
        assert conn.host == "192.168.1.1"
        assert conn.port == 22
        mock_client.set_missing_host_key_policy.assert_called()
        mock_client.connect.assert_called_once()

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_connect_with_ssh_key(self, mock_ssh_client_class):
        """测试 SSH 密钥认证连接"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        manager = SSHManager()
        conn = manager.connect(
            host="192.168.1.1",
            username="admin",
            ssh_key_path="~/.ssh/id_rsa"
        )
        
        call_kwargs = mock_client.connect.call_args[1]
        assert "key_filename" in call_kwargs
        assert "password" not in call_kwargs

    def test_connect_no_auth(self):
        """测试无认证方式时抛出异常"""
        manager = SSHManager()
        
        with pytest.raises(ValueError, match="必须提供密码或 SSH 密钥"):
            manager.connect(host="192.168.1.1", username="admin")

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_connect_device(self, mock_ssh_client_class):
        """测试 connect_device 简化方法"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        manager = SSHManager()
        conn = manager.connect_device(
            host="192.168.1.1",
            port=22,
            username="admin",
            password="secret"
        )
        
        assert conn.host == "192.168.1.1"

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_test_connection_success(self, mock_ssh_client_class):
        """测试连接测试成功"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        mock_stdout = Mock()
        mock_stdout.read.return_value = b"connection_test_ok"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = Mock()
        mock_stderr.read.return_value = b""
        
        mock_client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)
        
        manager = SSHManager()
        success, message = manager.test_connection(
            host="192.168.1.1",
            username="admin",
            password="secret"
        )
        
        assert success == True
        assert "成功" in message

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_test_connection_failure(self, mock_ssh_client_class):
        """测试连接测试失败"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        mock_stdout = Mock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_stderr = Mock()
        mock_stderr.read.return_value = b"Authentication failed"
        
        mock_client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)
        
        manager = SSHManager()
        success, message = manager.test_connection(
            host="192.168.1.1",
            username="admin",
            password="wrong"
        )
        
        assert success == False
        assert "失败" in message

    @patch("app.core.ssh_manager.paramiko.SSHClient")
    def test_execute_on_device(self, mock_ssh_client_class):
        """测试在设备上执行命令"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        
        mock_stdout = Mock()
        mock_stdout.read.return_value = b"result"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = Mock()
        mock_stderr.read.return_value = b""
        
        mock_client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)
        
        manager = SSHManager()
        stdout, stderr, code = manager.execute_on_device(
            host="192.168.1.1",
            port=22,
            username="admin",
            command="ls",
            password="secret"
        )
        
        assert code == 0
        assert stdout == "result"
        mock_client.close.assert_called()

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = SSHManager(max_connections=20)
        
        assert manager.max_connections == 20
        assert manager.pool is not None

    def test_close_all(self):
        """测试关闭所有连接"""
        manager = SSHManager()
        manager.close_all()
        
        assert manager.pool is not None  # pool 已关闭
