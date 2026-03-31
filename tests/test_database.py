"""
test_database.py - 数据库操作测试
"""

import pytest
import tempfile
from pathlib import Path
from sqlmodel import create_engine, Session
from app.data.models import Device, DeviceHistory


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def device_db_with_temp_engine(temp_db):
    """创建使用临时数据库的 DeviceDB 实例"""
    from app.data.database import DeviceDB
    
    # 使用 sqlmodel 的 create_all 创建表
    engine = create_engine(f"sqlite:///{temp_db}")
    
    # 创建所有表
    Device.metadata.create_all(engine)
    
    db = DeviceDB()
    db.engine = engine
    
    return db


class TestDeviceDB:
    """DeviceDB 数据库操作测试"""

    def test_add_device(self, device_db_with_temp_engine):
        """测试添加设备"""
        device = Device(
            name="test-server",
            device_type="server",
            ip_address="192.168.1.100",
            username="admin",
            password="secret",
            group="test-group"
        )
        
        device_id = device_db_with_temp_engine.add_device(device)
        
        assert device_id is not None
        assert device_id > 0

    def test_get_device(self, device_db_with_temp_engine):
        """测试获取设备"""
        device = Device(
            name="test-server",
            device_type="server",
            ip_address="192.168.1.100",
            username="admin"
        )
        device_id = device_db_with_temp_engine.add_device(device)
        
        retrieved = device_db_with_temp_engine.get_device(device_id)
        
        assert retrieved is not None
        assert retrieved.name == "test-server"
        assert retrieved.ip_address == "192.168.1.100"

    def test_get_device_not_found(self, device_db_with_temp_engine):
        """测试获取不存在的设备"""
        result = device_db_with_temp_engine.get_device(9999)
        assert result is None

    def test_get_all_devices(self, device_db_with_temp_engine):
        """测试获取所有设备"""
        for i in range(3):
            device = Device(
                name=f"server-{i}",
                device_type="server",
                ip_address=f"192.168.1.{i+1}",
                username="admin"
            )
            device_db_with_temp_engine.add_device(device)
        
        devices = device_db_with_temp_engine.get_all_devices()
        
        assert len(devices) == 3

    def test_get_devices_by_type(self, device_db_with_temp_engine):
        """测试按类型获取设备"""
        device_db_with_temp_engine.add_device(Device(
            name="server-1", device_type="server",
            ip_address="192.168.1.1", username="a"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="switch-1", device_type="switch",
            ip_address="192.168.1.2", username="a"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="server-2", device_type="server",
            ip_address="192.168.1.3", username="a"
        ))
        
        servers = device_db_with_temp_engine.get_devices_by_type("server")
        switches = device_db_with_temp_engine.get_devices_by_type("switch")
        
        assert len(servers) == 2
        assert len(switches) == 1

    def test_get_devices_by_group(self, device_db_with_temp_engine):
        """测试按分组获取设备"""
        device_db_with_temp_engine.add_device(Device(
            name="server-1", device_type="server",
            ip_address="192.168.1.1", username="a", group="group-a"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="server-2", device_type="server",
            ip_address="192.168.1.2", username="a", group="group-b"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="server-3", device_type="server",
            ip_address="192.168.1.3", username="a", group="group-a"
        ))
        
        group_a = device_db_with_temp_engine.get_devices_by_group("group-a")
        
        assert len(group_a) == 2

    def test_update_device(self, device_db_with_temp_engine):
        """测试更新设备"""
        device = Device(
            name="old-name",
            device_type="server",
            ip_address="192.168.1.1",
            username="admin"
        )
        device_id = device_db_with_temp_engine.add_device(device)
        
        success = device_db_with_temp_engine.update_device(
            device_id,
            name="new-name",
            ip_address="192.168.2.1"
        )
        
        assert success == True
        updated = device_db_with_temp_engine.get_device(device_id)
        assert updated.name == "new-name"
        assert updated.ip_address == "192.168.2.1"

    def test_update_device_not_found(self, device_db_with_temp_engine):
        """测试更新不存在的设备"""
        success = device_db_with_temp_engine.update_device(9999, name="new-name")
        assert success == False

    def test_delete_device(self, device_db_with_temp_engine):
        """测试删除设备"""
        device = Device(
            name="to-delete",
            device_type="server",
            ip_address="192.168.1.1",
            username="admin"
        )
        device_id = device_db_with_temp_engine.add_device(device)
        
        success = device_db_with_temp_engine.delete_device(device_id)
        
        assert success == True
        assert device_db_with_temp_engine.get_device(device_id) is None

    def test_delete_device_not_found(self, device_db_with_temp_engine):
        """测试删除不存在的设备"""
        success = device_db_with_temp_engine.delete_device(9999)
        assert success == False

    def test_get_all_groups(self, device_db_with_temp_engine):
        """测试获取所有分组"""
        device_db_with_temp_engine.add_device(Device(
            name="s1", device_type="server",
            ip_address="1.1.1.1", username="a", group="group-a"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="s2", device_type="server",
            ip_address="1.1.1.2", username="a", group="group-b"
        ))
        device_db_with_temp_engine.add_device(Device(
            name="s3", device_type="server",
            ip_address="1.1.1.3", username="a", group=None
        ))
        
        groups = device_db_with_temp_engine.get_all_groups()
        
        assert "group-a" in groups
        assert "group-b" in groups
        assert len(groups) == 2
