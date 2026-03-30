"""
app/plugins/switch_info.py - 交换机信息插件

获取交换机信息:
- 端口状态
- VLAN 信息
- 带宽利用率
"""

from app.core.card_plugin import (
    BaseCardPlugin, PluginInfo, 
    register_plugin
)


@register_plugin
class SwitchInfoPlugin(BaseCardPlugin):
    """交换机信息插件"""
    
    info = PluginInfo(
        name="switch_info",
        version="1.0.0",
        description="获取交换机端口和 VLAN 信息",
        icon="🔌",
        supported_types=["switch"],
        priority=10
    )
    
    def fetch(self, ssh_conn) -> dict:
        """获取交换机信息"""
        result = {
            "port_count": 0,
            "active_ports": 0,
            "vlan_name": None,
            "up_ports": [],
        }
        
        try:
            # 尝试多种交换机命令
            # 华为/H3C 风格
            for cmd in [
                "display interface brief | include Gigabit|40GE",
                "show interfaces status",
                "ip link show",
            ]:
                stdout, _, code = ssh_conn.execute(cmd)
                if code == 0 and stdout.strip():
                    result["raw_output"] = stdout
                    # 统计 up 状态的端口
                    lines = stdout.split("\n")
                    up_count = 0
                    for line in lines:
                        if "UP" in line.upper() or "connected" in line.lower():
                            up_count += 1
                    if up_count > 0:
                        result["active_ports"] = up_count
                        result["port_count"] = len(lines)
                    break
            
            # 获取 VLAN 信息
            for cmd in [
                "display vlan | include Name",
                "show vlan",
            ]:
                stdout, _, code = ssh_conn.execute(cmd)
                if code == 0 and stdout.strip():
                    result["vlan_info"] = stdout.strip()[:200]
                    break
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def render(self, data: dict) -> list:
        """渲染交换机信息"""
        items = []
        
        if data.get("active_ports", 0) > 0:
            items.append({
                "label": "活跃端口",
                "value": f"{data['active_ports']}/{data.get('port_count', '?')}",
                "icon": "🔌"
            })
        
        if data.get("vlan_info"):
            # 简化显示
            vlan = data["vlan_info"].split("\n")[0][:30]
            items.append({
                "label": "VLAN",
                "value": vlan,
                "icon": "🏷️"
            })
        
        return items
