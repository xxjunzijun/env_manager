"""
tests/test_card_grid.py - CardGrid 模块测试
"""
import pytest
from unittest.mock import MagicMock
from app.data.models import Device
from app.ui.card_grid import DeviceCardGrid, DeviceListView


@pytest.fixture
def mock_device():
    return Device(
        id=1,
        name="test-server",
        ip_address="192.168.1.100",
        port=22,
        username="admin",
        password="password",
        device_type="server",
        group_name="default",
        tags="test",
    )


@pytest.fixture
def mock_devices():
    return [
        Device(
            id=i,
            name=f"server-{i}",
            ip_address=f"192.168.1.{100+i}",
            port=22,
            username="admin",
            password="password",
            device_type="server",
            group_name="default",
            tags="test",
        )
        for i in range(1, 4)
    ]


class TestDeviceCardGrid:
    def test_grid_initialization(self):
        """网格容器初始化"""
        grid = DeviceCardGrid()
        assert grid is not None
        assert isinstance(grid.grid, __import__('flet').Row)
        assert grid.grid.wrap is True
        assert grid.grid.spacing == 16
        assert grid.grid.run_spacing == 16

    def test_set_devices(self, mock_devices):
        """设置设备列表"""
        grid = DeviceCardGrid()
        grid.set_devices(mock_devices)
        # 卡片数 = 设备数（AddDeviceCard 单独处理）
        assert len(grid.devices) == 3

    def test_set_devices_empty(self):
        """空设备列表"""
        grid = DeviceCardGrid()
        grid.set_devices([])
        assert len(grid.devices) == 0

    def test_set_devices_replaces_old(self, mock_devices, mock_device):
        """set_devices 替换旧列表"""
        grid = DeviceCardGrid()
        grid.set_devices([mock_device])
        assert len(grid.devices) == 1
        grid.set_devices(mock_devices)
        assert len(grid.devices) == 3

    def test_add_device_card_hidden_when_no_callback(self):
        """无 on_add_click 时不显示添加卡片"""
        grid = DeviceCardGrid()
        assert grid.add_card is None

    def test_add_device_card_shown_when_callback_provided(self):
        """提供 on_add_click 时显示添加卡片"""
        on_add = MagicMock()
        grid = DeviceCardGrid(on_add_click=on_add)
        assert grid.add_card is not None

    def test_on_reorder_callback(self, mock_devices):
        """拖拽排序回调"""
        callback = MagicMock()
        grid = DeviceCardGrid(devices=mock_devices, on_reorder=callback)
        assert grid.on_reorder == callback

    def test_drag_state_initialization(self):
        """拖拽状态初始为空"""
        grid = DeviceCardGrid()
        assert grid._drag_source_index is None

    def test_grid_alignment_is_main_axis_start(self):
        """对齐方式为 MainAxisAlignment.START"""
        grid = DeviceCardGrid()
        assert grid.grid.alignment == __import__('flet').MainAxisAlignment.START

    def test_grid_expand_true(self):
        """网格容器 expand=True"""
        grid = DeviceCardGrid()
        assert grid.expand is True


class TestDeviceListView:
    def test_listview_initialization(self):
        """列表视图初始化"""
        lv = DeviceListView()
        assert lv is not None
        assert isinstance(lv, __import__('flet').ListView)

    def test_set_devices(self, mock_devices):
        """设置设备列表"""
        lv = DeviceListView()
        lv.set_devices(mock_devices)
        assert len(lv.devices) == 3

    def test_set_devices_empty(self):
        """空设备列表"""
        lv = DeviceListView()
        lv.set_devices([])
        assert len(lv.devices) == 0

    def test_add_card_hidden_when_no_callback(self):
        """无 on_add_click 时不显示添加卡片"""
        lv = DeviceListView()
        assert lv.add_card is None

    def test_add_card_shown_when_callback_provided(self):
        """提供 on_add_click 时显示添加卡片"""
        on_add = MagicMock()
        lv = DeviceListView(on_add_click=on_add)
        assert lv.add_card is not None
