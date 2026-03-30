"""
app/core/card_plugin.py - 卡片插件基类

卡片扩展机制:
1. 所有插件继承 BaseCardPlugin
2. 插件通过 @register_plugin 注册
3. 卡片渲染时自动调用所有插件的 fetch 和 render 方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from app.utils.logger import get_logger

logger = get_logger("plugin")


@dataclass
class CardData:
    """卡片数据容器"""
    device_id: int
    device_type: str  # server / switch
    plugin_data: Dict[str, Any] = field(default_factory=dict)
    
    def set(self, key: str, value: Any):
        """设置插件数据"""
        self.plugin_data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取插件数据"""
        return self.plugin_data.get(key, default)


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    icon: str  # emoji 或图标名称
    supported_types: List[str]  # ["server", "switch"] 或 ["server"]
    priority: int = 100  # 优先级，数字越小越靠前


class BaseCardPlugin(ABC):
    """
    卡片插件基类
    
    子类需要实现:
    - fetch(): 获取数据
    - render(): 渲染数据为卡片显示项
    """
    
    info: PluginInfo
    
    @abstractmethod
    def fetch(self, ssh_conn) -> Dict[str, Any]:
        """
        通过 SSH 获取数据
        
        Args:
            ssh_conn: SSH 连接对象 (SSHConnection)
            
        Returns:
            Dict: 插件数据，如 {"cpu_usage": 45.5, "memory_usage": 62.3}
        """
        pass
    
    @abstractmethod
    def render(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        将数据渲染为卡片显示项
        
        Args:
            data: fetch() 返回的数据
            
        Returns:
            List[Dict]: 显示项列表，如 [
                {"label": "CPU", "value": "45%", "icon": "[STAT]"},
                {"label": "内存", "value": "62%", "icon": "[MEM]"}
            ]
        """
        pass
    
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return self.info


class CardPluginRegistry:
    """
    卡片插件注册表
    
    管理所有已注册的插件
    """
    
    _plugins: Dict[str, BaseCardPlugin] = {}
    _device_type_plugins: Dict[str, List[BaseCardPlugin]] = {}
    
    @classmethod
    def register(cls, plugin: BaseCardPlugin) -> None:
        """注册插件"""
        info = plugin.get_info()
        cls._plugins[info.name] = plugin
        
        # 按设备类型分组
        for device_type in info.supported_types:
            if device_type not in cls._device_type_plugins:
                cls._device_type_plugins[device_type] = []
            cls._device_type_plugins[device_type].append(plugin)
        
        # 按优先级排序
        cls._device_type_plugins[device_type].sort(
            key=lambda p: p.get_info().priority
        )
        
        logger.info(f"插件注册: {info.name} v{info.version} ({', '.join(info.supported_types)})")
    
    @classmethod
    def get_plugin(cls, name: str) -> Optional[BaseCardPlugin]:
        """获取插件"""
        return cls._plugins.get(name)
    
    @classmethod
    def get_plugins_for_type(cls, device_type: str) -> List[BaseCardPlugin]:
        """获取指定设备类型的插件"""
        return cls._device_type_plugins.get(device_type, [])
    
    @classmethod
    def get_all_plugins(cls) -> Dict[str, BaseCardPlugin]:
        """获取所有插件"""
        return cls._plugins.copy()
    
    @classmethod
    def list_plugins(cls) -> List[PluginInfo]:
        """列出所有插件信息"""
        return [p.get_info() for p in cls._plugins.values()]


def register_plugin(cls):
    """插件注册装饰器"""
    def register():
        plugin_instance = cls()
        CardPluginRegistry.register(plugin_instance)
    register()
    return cls
