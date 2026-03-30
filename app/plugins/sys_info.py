"""
app/plugins/sys_info.py - 系统信息插件

获取服务器系统信息:
- CPU 使用率
- 内存使用率
- 磁盘使用率
- 运行时间
- 负载
"""

import re
from app.core.card_plugin import (
    BaseCardPlugin, PluginInfo, CardData, 
    register_plugin
)


@register_plugin
class SysInfoPlugin(BaseCardPlugin):
    """系统信息插件"""
    
    info = PluginInfo(
        name="sys_info",
        version="1.0.0",
        description="获取服务器系统信息",
        icon="🖥️",
        supported_types=["server"],
        priority=10
    )
    
    def fetch(self, ssh_conn) -> dict:
        """获取系统信息"""
        result = {
            "cpu_usage": None,
            "memory_usage": None,
            "disk_usage": None,
            "uptime": None,
            "load_avg": None,
            "hostname": None,
        }
        
        try:
            # 获取 CPU 和内存使用率
            # Linux: 使用 top 或 free
            stdout, _, _ = ssh_conn.execute("free | grep Mem")
            if stdout:
                parts = stdout.split()
                if len(parts) >= 7:
                    total = int(parts[1])
                    used = int(parts[2])
                    if total > 0:
                        result["memory_usage"] = round(used / total * 100, 1)
            
            # CPU 使用率 (通过 /proc/stat 计算)
            stdout, _, _ = ssh_conn.execute("cat /proc/stat | head -1")
            if stdout:
                # 简化计算：获取 idle 百分比
                pass  # 实际实现需要计算差值
            
            # 获取负载
            stdout, _, _ = ssh_conn.execute("cat /proc/loadavg")
            if stdout:
                parts = stdout.strip().split()
                result["load_avg"] = " ".join(parts[:3])
            
            # 获取运行时间
            stdout, _, _ = ssh_conn.execute("uptime -s")
            if stdout:
                result["uptime"] = stdout.strip()
            
            # 获取主机名
            stdout, _, _ = ssh_conn.execute("hostname")
            if stdout:
                result["hostname"] = stdout.strip()
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def render(self, data: dict) -> list:
        """渲染系统信息"""
        items = []
        
        if data.get("hostname"):
            items.append({
                "label": "主机名",
                "value": data["hostname"],
                "icon": "🏷️"
            })
        
        if data.get("load_avg"):
            items.append({
                "label": "负载",
                "value": data["load_avg"],
                "icon": "📈"
            })
        
        if data.get("memory_usage") is not None:
            items.append({
                "label": "内存",
                "value": f"{data['memory_usage']}%",
                "icon": "💾"
            })
        
        if data.get("uptime"):
            items.append({
                "label": "运行时间",
                "value": data["uptime"][:10],  # 只显示日期
                "icon": "⏱️"
            })
        
        if data.get("error"):
            items.append({
                "label": "错误",
                "value": data["error"][:30],
                "icon": "❌"
            })
        
        return items


@register_plugin
class BasicInfoPlugin(BaseCardPlugin):
    """基础信息插件 - 所有设备通用"""
    
    info = PluginInfo(
        name="basic_info",
        version="1.0.0",
        description="获取设备基础信息",
        icon="📋",
        supported_types=["server", "switch"],
        priority=1  # 最优先显示
    )
    
    def fetch(self, ssh_conn) -> dict:
        """获取基础信息"""
        result = {
            "os_version": None,
            "kernel": None,
            "ssh_status": True,
        }
        
        try:
            # 获取 OS 版本
            for cmd in ["cat /etc/os-release", "uname -a", "cat /etc/issue"]:
                stdout, _, code = ssh_conn.execute(cmd)
                if code == 0 and stdout.strip():
                    result["os_version"] = stdout.strip()[:100]
                    break
            
            # 获取内核版本
            stdout, _, _ = ssh_conn.execute("uname -r")
            if stdout:
                result["kernel"] = stdout.strip()
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def render(self, data: dict) -> list:
        """渲染基础信息"""
        items = []
        
        if data.get("os_version"):
            # 提取 NAME= 和 VERSION=
            lines = data["os_version"].split("\n")
            name = version = ""
            for line in lines:
                if line.startswith("PRETTY_NAME="):
                    name = line.split("=")[1].strip('"')
                elif line.startswith("NAME="):
                    name = line.split("=")[1].strip('"')
                elif line.startswith("VERSION="):
                    version = line.split("=")[1].strip('"')
            
            display = name or (version if len(version) < 30 else version[:27] + "...")
            items.append({
                "label": "系统",
                "value": display,
                "icon": "🖥️"
            })
        
        if data.get("kernel"):
            items.append({
                "label": "内核",
                "value": data["kernel"],
                "icon": "⚙️"
            })
        
        return items
