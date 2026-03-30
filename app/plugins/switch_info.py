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
from app.utils.logger import get_logger


logger = get_logger("plugin.switch")


@register_plugin
class SwitchInfoPlugin(BaseCardPlugin):
    """交换机信息插件"""
    
    info = PluginInfo(
        name="switch_info",
        version="1.0.0",
        description="获取交换机端口和 VLAN 信息",
        icon="[SW]",
        supported_types=["switch"],
        priority=10
    )
    
    def fetch(self, ssh_conn) -> dict:
        """获取交换机信息"""
        logger.debug("SwitchInfoPlugin.fetch() 开始执行")
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
                        logger.debug(f"活跃端口: {result['active_ports']}/{result['port_count']}")
                    break
            
            # 获取 VLAN 信息
            for cmd in [
                "display vlan | include Name",
                "show vlan",
            ]:
                stdout, _, code = ssh_conn.execute(cmd)
                if code == 0 and stdout.strip():
                    result["vlan_info"] = stdout.strip()[:200]
                    logger.debug(f"VLAN 信息: {result['vlan_info'][:50]}...")
                    break
                    
        except Exception as e:
            logger.error(f"SwitchInfoPlugin.fetch() 异常: {e}")
            result["error"] = str(e)
        
        return result
    
    def render(self, data: dict) -> list:
        """渲染交换机信息"""
        items = []
        
        if data.get("active_ports", 0) > 0:
            items.append({
                "label": "活跃端口",
                "value": f"{data['active_ports']}/{data.get('port_count', '?')}",
                "icon": "[PORT]"
            })
        
        if data.get("vlan_info"):
            # 简化显示
            vlan = data["vlan_info"].split("\n")[0][:30]
            items.append({
                "label": "VLAN",
                "value": vlan,
                "icon": "[VLAN]"
            })
        
        return items
