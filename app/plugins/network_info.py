"""
app/plugins/network_info.py - 网络信息插件

获取网络信息:
- IP 地址
- 网络接口状态
- 连接数
"""

from app.core.card_plugin import (
    BaseCardPlugin, PluginInfo, 
    register_plugin
)


@register_plugin
class NetworkInfoPlugin(BaseCardPlugin):
    """网络信息插件"""
    
    info = PluginInfo(
        name="network_info",
        version="1.0.0",
        description="获取网络配置信息",
        icon="🌐",
        supported_types=["server"],
        priority=20
    )
    
    def fetch(self, ssh_conn) -> dict:
        """获取网络信息"""
        result = {
            "ip_address": None,
            "default_gateway": None,
            "dns_servers": [],
            "tcp_connections": 0,
        }
        
        try:
            # 获取 IP 地址
            stdout, _, _ = ssh_conn.execute(
                "ip -4 addr show | grep inet | grep -v 127.0.0.1 | awk '{print $2}' | head -1"
            )
            if stdout.strip():
                result["ip_address"] = stdout.strip()
            
            # 获取默认网关
            stdout, _, _ = ssh_conn.execute("ip route | grep default | awk '{print $3}' | head -1")
            if stdout.strip():
                result["default_gateway"] = stdout.strip()
            
            # 获取 DNS 服务器
            stdout, _, _ = ssh_conn.execute("cat /etc/resolv.conf | grep nameserver | awk '{print $2}'")
            if stdout.strip():
                result["dns_servers"] = stdout.strip().split("\n")[:2]
            
            # 获取 TCP 连接数
            stdout, _, _ = ssh_conn.execute("ss -tn | grep ESTAB | wc -l")
            if stdout.strip():
                result["tcp_connections"] = int(stdout.strip())
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def render(self, data: dict) -> list:
        """渲染网络信息"""
        items = []
        
        if data.get("ip_address"):
            items.append({
                "label": "IP",
                "value": data["ip_address"],
                "icon": "📍"
            })
        
        if data.get("default_gateway"):
            items.append({
                "label": "网关",
                "value": data["default_gateway"],
                "icon": "🚪"
            })
        
        if data.get("tcp_connections", 0) > 0:
            items.append({
                "label": "连接",
                "value": str(data["tcp_connections"]),
                "icon": "🔗"
            })
        
        if data.get("dns_servers"):
            items.append({
                "label": "DNS",
                "value": ", ".join(data["dns_servers"]),
                "icon": "📡"
            })
        
        return items
