"""
app/plugins/stub_plugin.py - Demo 模式打桩插件

当设备类型为 "demo" 或设备名含 "demo" 时使用此插件，
返回模拟数据而不进行真实 SSH 连接。
"""

from app.core.card_plugin import (
    BaseCardPlugin, PluginInfo,
    register_plugin
)
from app.utils.logger import get_logger


logger = get_logger("plugin.stub")


@register_plugin
class StubPlugin(BaseCardPlugin):
    """Demo 模式打桩插件"""
    
    info = PluginInfo(
        name="stub",
        version="1.0.0",
        description="Demo 模式打桩插件，返回模拟数据",
        icon="[DEMO]",
        supported_types=["demo", "server", "switch"],
        priority=0  # 高优先级，优先匹配 demo 模式
    )
    
    def fetch(self, ssh_conn) -> dict:
        """
        返回模拟数据
        
        注意：ssh_conn 参数在此插件中被忽略
        """
        logger.debug("StubPlugin.fetch() 返回模拟数据")
        
        # 模拟数据
        return {
            "hostname": "stub-server",
            "cpu": "50%",
            "memory": "4GB/8GB",
            "disk": "100GB/500GB",
            "is_stub": True,
        }
    
    def render(self, data: dict) -> list:
        """渲染模拟数据"""
        items = [
            {
                "label": "主机名",
                "value": data.get("hostname", "N/A"),
                "icon": "[HOST]"
            },
            {
                "label": "CPU",
                "value": data.get("cpu", "N/A"),
                "icon": "[CPU]"
            },
            {
                "label": "内存",
                "value": data.get("memory", "N/A"),
                "icon": "[MEM]"
            },
            {
                "label": "磁盘",
                "value": data.get("disk", "N/A"),
                "icon": "[DISK]"
            },
        ]
        return items
