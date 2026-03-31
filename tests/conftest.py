"""
conftest.py - pytest fixtures
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_device_data():
    """样例设备数据"""
    return {
        "name": "test-server-01",
        "device_type": "server",
        "ip_address": "192.168.1.100",
        "port": 22,
        "username": "admin",
        "password": "test_password",
        "group": "test-group",
        "tags": "linux,production",
        "description": "测试服务器",
    }


@pytest.fixture
def sample_switch_data():
    """样例交换机数据"""
    return {
        "name": "test-switch-01",
        "device_type": "switch",
        "ip_address": "192.168.1.1",
        "port": 22,
        "username": "admin",
        "password": "test_password",
        "group": "network",
        "tags": "cisco,huawei",
    }
