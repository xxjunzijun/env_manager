"""
app/plugins/__init__.py

插件模块

自动导入以注册所有插件
"""

from app.plugins import sys_info
from app.plugins import network_info
from app.plugins import switch_info
from app.plugins import stub_plugin

# 插件列表:
# - sys_info: 系统信息插件 (CPU, 内存, 负载)
# - network_info: 网络信息插件 (IP, 网关, 连接数)
# - switch_info: 交换机信息插件 (端口状态, VLAN)
# - stub_plugin: Demo 模式打桩插件 (模拟数据)

__all__ = [
    "sys_info",
    "network_info", 
    "switch_info",
    "stub_plugin",
]
