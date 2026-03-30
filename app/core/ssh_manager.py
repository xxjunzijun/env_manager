"""
app/core/ssh_manager.py - SSH 连接管理

支持:
- 密码认证
- 密钥认证
- 连接池
- 连接复用
"""

import os
import paramiko
from typing import Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future
from app.utils.logger import get_logger


# 获取子 Logger
logger = get_logger("ssh")


class SSHConnection:
    """SSH 连接包装类"""
    
    def __init__(self, client: paramiko.SSHClient, host: str, port: int):
        self.client = client
        self.host = host
        self.port = port
        self.is_connected = True
        logger.debug(f"SSH 连接创建: {host}:{port}")
    
    def execute(self, command: str) -> tuple[str, str, int]:
        """执行命令
        
        Returns:
            (stdout, stderr, exit_code)
        """
        if not self.is_connected:
            logger.warning(f"执行失败 - 连接已关闭: {self.host}")
            return "", "Not connected", 1
        
        try:
            logger.debug(f"执行命令: {command[:100]}...")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8", errors="ignore")
            stderr_text = stderr.read().decode("utf-8", errors="ignore")
            
            if exit_code == 0:
                logger.debug(f"命令执行成功: exit_code={exit_code}, output长度={len(stdout_text)}")
            else:
                logger.warning(f"命令执行返回非零: exit_code={exit_code}")
            
            return stdout_text, stderr_text, exit_code
        except Exception as e:
            logger.error(f"执行命令异常: {e}")
            return "", str(e), 1
    
    def close(self):
        """关闭连接"""
        if self.is_connected:
            self.client.close()
            self.is_connected = False
            logger.debug(f"SSH 连接关闭: {self.host}:{self.port}")


class SSHManager:
    """
    SSH 连接管理器
    
    支持连接池和并发连接
    """
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = ThreadPoolExecutor(max_workers=max_connections)
        self._connections: Dict[tuple, SSHConnection] = {}
        logger.info(f"SSHManager 初始化: 最大连接数={max_connections}")
    
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
                expand_key_path = os.path.expanduser(ssh_key_path)
                logger.debug(f"使用 SSH 密钥: {expand_key_path}")
                connect_kwargs["key_filename"] = expand_key_path
            elif password:
                connect_kwargs["password"] = password
            else:
                logger.error("连接失败: 必须提供密码或 SSH 密钥")
                raise ValueError("必须提供密码或 SSH 密钥")
            
            # 执行连接
            logger.debug(f"连接参数: host={host}, port={port}, username={username}")
            client.connect(**connect_kwargs)
            conn = SSHConnection(client, host, port)
            logger.info(f"SSH 连接成功: {host}:{port}")
            return conn
            
        except Exception as e:
            logger.error(f"SSH 连接失败: {host}:{port} - {str(e)}")
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
        logger.info(f"测试连接: {username}@{host}:{port}")
        
        try:
            conn = self.connect(host, port, username, password, ssh_key_path, timeout)
            stdout, stderr, code = conn.execute("echo 'connection_test_ok'")
            conn.close()
            
            if code == 0:
                logger.info(f"连接测试成功: {host}:{port}")
                return True, "连接成功"
            else:
                error_msg = stderr[:100] if stderr else "未知错误"
                logger.warning(f"连接测试失败: {host}:{port} - {error_msg}")
                return False, f"连接失败: {error_msg}"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"连接测试异常: {host}:{port} - {error_msg}")
            return False, f"连接失败: {error_msg}"
    
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
        logger.debug(f"远程执行: {username}@{host}:{port} - {command[:80]}...")
        
        try:
            conn = self.connect(host, port, username, password, ssh_key_path)
            result = conn.execute(command)
            conn.close()
            
            stdout, stderr, code = result
            if code == 0:
                logger.debug(f"远程执行成功: exit_code={code}")
            else:
                logger.warning(f"远程执行返回非零: exit_code={code}, stderr={stderr[:50]}")
            
            return result
        except Exception as e:
            logger.error(f"远程执行异常: {e}")
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
        logger.debug(f"异步执行提交: {host}:{port}")
        
        future = self.pool.submit(
            self.execute_on_device,
            host, port, username, command, password, ssh_key_path
        )
        
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
            logger.debug(f"异步执行回调已注册: {host}:{port}")
        
        return future
    
    def close_all(self):
        """关闭所有连接"""
        logger.info("关闭所有 SSH 连接...")
        for key, conn in self._connections.items():
            conn.close()
        self._connections.clear()
        self.pool.shutdown(wait=True)
        logger.info("所有 SSH 连接已关闭")


# 全局 SSH 管理器实例
ssh_manager = SSHManager()
