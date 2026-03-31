"""
test_models.py - Device 模型测试
"""

import pytest
from datetime import datetime
from app.data.models import Device, DeviceHistory


class TestDeviceModel:
    """Device 模型测试"""

    def test_device_creation(self, sample_device_data):
        """测试设备创建"""
        device = Device(**sample_device_data)
        
        assert device.name == "test-server-01"
        assert device.device_type == "server"
        assert device.ip_address == "192.168.1.100"
        assert device.port == 22
        assert device.username == "admin"
        assert device.group == "test-group"
        assert device.is_online == False

    def test_device_tags_list(self, sample_device_data):
        """测试 tags_list 属性"""
        device = Device(**sample_device_data)
        
        tags = device.tags_list
        assert len(tags) == 2
        assert "linux" in tags
        assert "production" in tags

    def test_device_tags_list_empty(self):
        """测试空 tags"""
        device = Device(name="test", device_type="server", ip_address="1.1.1.1", username="a")
        assert device.tags_list == []

    def test_device_tags_list_with_spaces(self):
        """测试 tags 带空格"""
        device = Device(name="test", device_type="server", ip_address="1.1.1.1", username="a", tags=" a , b , c ")
        tags = device.tags_list
        assert tags == ["a", "b", "c"]

    def test_device_display_type(self, sample_device_data, sample_switch_data):
        """测试 display_type 属性"""
        server = Device(**sample_device_data)
        switch = Device(**sample_switch_data)
        
        assert server.display_type == "服务器"
        assert switch.display_type == "交换机"

    def test_device_ext_data(self):
        """测试 ext_data 属性"""
        device = Device(
            name="test",
            device_type="server",
            ip_address="1.1.1.1",
            username="a",
            ext_info='{"cpu": 50, "mem": 80}'
        )
        
        data = device.ext_data
        assert data["cpu"] == 50
        assert data["mem"] == 80

    def test_device_ext_data_invalid_json(self):
        """测试 ext_data 无效 JSON"""
        device = Device(
            name="test",
            device_type="server",
            ip_address="1.1.1.1",
            username="a",
            ext_info="invalid json"
        )
        
        data = device.ext_data
        assert data == {}

    def test_device_default_values(self):
        """测试默认值"""
        device = Device(name="test", device_type="server", ip_address="1.1.1.1", username="a")
        
        assert device.port == 22
        assert device.tags == ""
        assert device.is_online == False
        assert device.last_check is None
        assert device.ext_info == "{}"

    def test_device_created_at_auto(self):
        """测试 created_at 自动生成"""
        before = datetime.now()
        device = Device(name="test", device_type="server", ip_address="1.1.1.1", username="a")
        after = datetime.now()
        
        assert before <= device.created_at <= after


class TestDeviceHistoryModel:
    """DeviceHistory 模型测试"""

    def test_history_creation(self):
        """测试历史记录创建"""
        history = DeviceHistory(
            device_id=1,
            is_online=True,
            cpu_usage=45.5,
            memory_usage=62.3,
            disk_usage=70.0,
        )
        
        assert history.device_id == 1
        assert history.is_online == True
        assert history.cpu_usage == 45.5
        assert history.memory_usage == 62.3
        assert history.disk_usage == 70.0
        assert history.status_message is None

    def test_history_defaults(self):
        """测试历史记录默认值"""
        history = DeviceHistory(device_id=1)
        
        assert history.is_online == False
        assert history.cpu_usage is None
        assert history.memory_usage is None
        assert history.disk_usage is None
