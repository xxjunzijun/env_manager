"""
test_plugins.py - 插件系统测试
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.core.card_plugin import (
    BaseCardPlugin, CardData, PluginInfo, 
    CardPluginRegistry, register_plugin
)
from app.plugins.sys_info import SysInfoPlugin, BasicInfoPlugin
from app.plugins.switch_info import SwitchInfoPlugin


class MockSSHConnection:
    """模拟 SSH 连接"""
    
    def __init__(self, outputs=None):
        self.outputs = outputs or {}
        self.call_count = {}
    
    def execute(self, command):
        # 记录调用
        cmd_key = command[:30]
        self.call_count[cmd_key] = self.call_count.get(cmd_key, 0) + 1
        
        # 返回预设输出
        if command in self.outputs:
            return (self.outputs[command], "", 0)
        return ("", "", 0)


class TestPluginInfo:
    """PluginInfo 测试"""

    def test_plugin_info_creation(self):
        """测试插件信息创建"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            icon="[TEST]",
            supported_types=["server"],
            priority=10
        )
        
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.supported_types == ["server"]
        assert info.priority == 10


class TestCardData:
    """CardData 测试"""

    def test_card_data_creation(self):
        """测试卡片数据创建"""
        card = CardData(device_id=1, device_type="server")
        
        assert card.device_id == 1
        assert card.device_type == "server"
        assert card.plugin_data == {}

    def test_card_data_set_get(self):
        """测试卡片数据存取"""
        card = CardData(device_id=1, device_type="server")
        
        card.set("cpu", 50)
        card.set("memory", 80)
        
        assert card.get("cpu") == 50
        assert card.get("memory") == 80
        assert card.get("disk", 0) == 0  # 默认值

    def test_card_data_defaults(self):
        """测试卡片数据默认值"""
        card = CardData(device_id=1, device_type="server")
        
        assert card.get("nonexistent") is None
        assert card.get("nonexistent", "default") == "default"


class TestCardPluginRegistry:
    """插件注册表测试"""

    def test_register_plugin(self):
        """测试插件注册"""
        # 清空注册表
        CardPluginRegistry._plugins.clear()
        CardPluginRegistry._device_type_plugins.clear()
        
        plugin = SysInfoPlugin()
        CardPluginRegistry.register(plugin)
        
        assert "sys_info" in CardPluginRegistry._plugins
        assert "server" in CardPluginRegistry._device_type_plugins

    def test_get_plugin(self):
        """测试获取插件"""
        CardPluginRegistry._plugins.clear()
        CardPluginRegistry._plugins["test"] = SysInfoPlugin()
        
        plugin = CardPluginRegistry.get_plugin("test")
        assert plugin is not None

    def test_get_plugins_for_type(self):
        """测试获取指定类型的插件"""
        CardPluginRegistry._device_type_plugins.clear()
        CardPluginRegistry._device_type_plugins["server"] = [SysInfoPlugin(), BasicInfoPlugin()]
        
        plugins = CardPluginRegistry.get_plugins_for_type("server")
        assert len(plugins) == 2

    def test_get_plugins_for_type_none(self):
        """测试获取不存在的类型"""
        plugins = CardPluginRegistry.get_plugins_for_type("nonexistent")
        assert plugins == []

    def test_list_plugins(self):
        """测试列出所有插件"""
        CardPluginRegistry._plugins.clear()
        CardPluginRegistry._plugins["sys_info"] = SysInfoPlugin()
        
        infos = CardPluginRegistry.list_plugins()
        assert len(infos) == 1
        assert infos[0].name == "sys_info"


class TestSysInfoPlugin:
    """SysInfo 插件测试"""

    def test_sys_info_fetch(self):
        """测试获取系统信息"""
        ssh = MockSSHConnection({
            "free | grep Mem": "Mem: 32768000 16384000 16384000 0 0 16384000\n",
            "cat /proc/loadavg": "0.52 0.48 0.45 1/1234 12345\n",
            "uptime -s": "2024-01-01 12:00:00\n",
            "hostname": "test-server\n",
        })
        
        plugin = SysInfoPlugin()
        result = plugin.fetch(ssh)
        
        assert result["memory_usage"] is not None
        assert result["load_avg"] is not None
        assert result["hostname"] == "test-server"

    def test_sys_info_render(self):
        """测试渲染系统信息"""
        data = {
            "hostname": "test-server",
            "load_avg": "0.52 0.48 0.45",
            "memory_usage": 50.0,
            "uptime": "2024-01-01 12:00:00",
        }
        
        plugin = SysInfoPlugin()
        items = plugin.render(data)
        
        assert len(items) >= 3
        labels = [item["label"] for item in items]
        assert "主机名" in labels
        assert "负载" in labels
        assert "内存" in labels

    def test_sys_info_render_with_error(self):
        """测试渲染带错误的数据"""
        data = {
            "error": "Connection timeout"
        }
        
        plugin = SysInfoPlugin()
        items = plugin.render(data)
        
        assert len(items) == 1
        assert items[0]["label"] == "错误"


class TestBasicInfoPlugin:
    """BasicInfo 插件测试"""

    def test_basic_info_fetch(self):
        """测试获取基础信息"""
        ssh = MockSSHConnection({
            "cat /etc/os-release": 'PRETTY_NAME="Ubuntu 22.04"\nVERSION="22.04"\n',
            "uname -r": "5.15.0-generic\n",
        })
        
        plugin = BasicInfoPlugin()
        result = plugin.fetch(ssh)
        
        assert result["ssh_status"] == True
        assert result["os_version"] is not None
        assert result["kernel"] == "5.15.0-generic"

    def test_basic_info_render(self):
        """测试渲染基础信息"""
        data = {
            "os_version": 'PRETTY_NAME="Ubuntu 22.04"\nVERSION="22.04"\n',
            "kernel": "5.15.0-generic",
        }
        
        plugin = BasicInfoPlugin()
        items = plugin.render(data)
        
        assert len(items) == 2
        labels = [item["label"] for item in items]
        assert "系统" in labels
        assert "内核" in labels


class TestSwitchInfoPlugin:
    """SwitchInfo 插件测试"""

    def test_switch_info_fetch(self):
        """测试获取交换机信息"""
        ssh = MockSSHConnection({
            "display interface brief | include Gigabit|40GE": "GigabitEthernet0/0/1 UP\nGigabitEthernet0/0/2 DOWN\n",
            "display vlan | include Name": "1 default\n",
        })
        
        plugin = SwitchInfoPlugin()
        result = plugin.fetch(ssh)
        
        assert result["active_ports"] >= 0

    def test_switch_info_render(self):
        """测试渲染交换机信息"""
        data = {
            "active_ports": 5,
            "port_count": 24,
            "vlan_info": "1 default\n2 vlan2",
        }
        
        plugin = SwitchInfoPlugin()
        items = plugin.render(data)
        
        assert len(items) == 2
        labels = [item["label"] for item in items]
        assert "活跃端口" in labels
        assert "VLAN" in labels

    def test_switch_info_render_no_data(self):
        """测试渲染空数据"""
        data = {}
        
        plugin = SwitchInfoPlugin()
        items = plugin.render(data)
        
        assert items == []
