"""
app/core/ssh_manager.py - SSH 连接管理

支持:
- 密码认证
- 密钥认证
- 连接池
- 连接复用
"""

import paramiko
import socket
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from app.utils.logger import setup_logger


logger = setup_logger("SSHManager")


class SSHConnection:
    """SSH 连接包装类"""
    
    def __init__(self, client: paramiko.SSHClient, host: str, port: int):
        self.client = client
        self.host = host
        self.port = port
        self.is_connected = True
    
    def execute(self, command: str) -> tuple[str, str, int]:
        """执行命令
        
        Returns:
            (stdout, stderr, exit_code)
        """
        if not self.is_connected:
            return "", "Not connected", 1
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            return (
                stdout.read().decode("utf-8", errors="ignore"),
                stderr.read().decode("utf-8", errors="ignore"),
                exit_code
            )
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return "", str(e), 1
    
    def close(self):
        """关闭连接"""
        if self.is_connected:
            self.client.close()
            self.is_connected = False


class SSHManager:
    """
    SSH 连接管理器
    
    支持连接池和并发连接
    """
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = ThreadPoolExecutor(max_workers=max_connections)
        self._connections = {}  # {(host, port, username): SSHConnection}
        self._lock = None  # 简化版，不使用锁
    
    def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
        timeout: int = 10
    ) -> SSHConnection:
        """
        建立 SSH 连接
        
        Args:
            host: IP 地址
            port: 端口
            username: 用户名
            password: 密码
            ssh_key_path: SSH 私钥路径
            timeout: 超时时间(秒)
            
        Returns:
            SSHConnection 对象
        """
        logger.info(f"正在连接 {username}@{host}:{port}...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 连接参数
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": timeout,
            }
            
            # 认证方式
            if ssh_key_path:
                connect_kwargs["key_filename"] = os.path.expanduser(ssh_key_path)
            elif password:
                connect_kwargs["password"] = password
            else:
                raise ValueError("必须提供密码或 SSH 密钥")
            
            client.connect(**connect_kwargs)
            conn = SSHConnection(client, host, port)
            logger.info(f"连接成功: {host}")
            return conn
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise
    
    def connect_device(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None
    ) -> SSHConnection:
        """连接设备（简化方法）"""
        return self.connect(host, port, username, password, ssh_key_path)
    
    def test_connection(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
        timeout: int = 10
    ) -> tuple[bool, str]:
        """
        测试连接
        
        Returns:
            (是否成功, 消息)
        """
        try:
            conn = self.connect(host, port, username, password, ssh_key_path, timeout)
            _, stderr, code = conn.execute("echo ok")
            conn.close()
            
            if code == 0:
                return True, "连接成功"
            else:
                return False, f"连接失败: {stderr[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def execute_on_device(
        self,
        host: str,
        port: int,
        username: str,
        command: str,
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None
    ) -> tuple[str, str, int]:
        """
        在设备上执行命令（自动连接和关闭）
        """
        try:
            conn = self.connect(host, port, username, password, ssh_key_path)
            result = conn.execute(command)
            conn.close()
            return result
        except Exception as e:
            return "", str(e), 1
    
    def async_execute(
        self,
        host: str,
        port: int,
        username: str,
        command: str,
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> Future:
        """
        异步执行命令
        
        Args:
            callback: 完成后的回调函数，签名为 (result_tuple)
        """
        future = self.pool.submit(
            self.execute_on_device,
            host, port, username, command, password, ssh_key_path
        )
        
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
        
        return future
    
    def close_all(self):
        """关闭所有连接"""
        for conn in self._connections.values():
            conn.close()
        self._connections.clear()
        self.pool.shutdown(wait=True)


# 全局 SSH 管理器实例
ssh_manager = SSHManager()
