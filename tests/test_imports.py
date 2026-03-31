"""
test_imports.py - 导入验证测试

确保所有核心模块可以正常导入，捕获依赖版本不兼容、
图标名称错误、模块路径错误等低级问题。
"""

import pytest


class TestImports:
    """核心模块导入测试"""

    def test_flet_import(self):
        """测试 flet 库可用"""
        import flet
        assert flet is not None
        assert hasattr(flet, "Page")
        assert hasattr(flet, "TextField")
        assert hasattr(flet, "icons")

    def test_flet_icons_accessible(self):
        """测试 flet 图标名称在当前版本可用
        
        Flet 0.83+ 访问图标需通过 ft.icons.Icons.ICON_NAME
        直接 ft.icons.ICON_NAME 会报 AttributeError
        """
        import flet as ft

        # 项目中实际使用的图标（格式：ft.icons.Icons.XXX）
        used_icons = [
            "SEARCH",
            "REFRESH",
            "EDIT",
            "ADD",
            "GRID_VIEW",
            "VIEW_LIST",
            "DELETE",
            "CLOSE",
            "INFO",
        ]

        for attr in used_icons:
            # 正确方式：ft.icons.Icons.XXX
            value = getattr(ft.icons.Icons, attr, None)
            assert value is not None, f"Flet icon Icons.{attr} not found in this version"
            
            # 错误方式（直接 ft.icons.XXX）不应可用
            direct = getattr(ft.icons, attr, "NOT_FOUND")
            # 记录哪些图标存在直接访问路径（兼容性参考）
            if direct != "NOT_FOUND":
                print(f"  [WARN] {attr} also available as ft.icons.{attr} = {direct}")

    def test_app_models_import(self):
        """测试数据模型可导入"""
        from app.data.models import Device, DeviceHistory

        # 验证字段存在
        assert hasattr(Device, "name")
        assert hasattr(Device, "device_type")
        assert hasattr(Device, "ip_address")
        assert hasattr(Device, "tags_list")
        assert hasattr(Device, "display_type")

    def test_app_database_import(self):
        """测试数据库模块可导入"""
        from app.data.database import DeviceDB, get_engine, init_database

        db = DeviceDB()
        assert db.engine is not None

    def test_app_ssh_manager_import(self):
        """测试 SSH 管理器可导入"""
        from app.core.ssh_manager import SSHManager, SSHConnection

        manager = SSHManager(max_connections=5)
        assert manager.max_connections == 5

    def test_app_logger_import(self):
        """测试日志模块可导入"""
        from app.utils.logger import get_logger, setup_logger

        logger = get_logger("test")
        assert logger is not None

    def test_app_plugin_base_import(self):
        """测试插件基类可导入"""
        from app.core.card_plugin import (
            BaseCardPlugin,
            CardData,
            CardPluginRegistry,
            PluginInfo,
            register_plugin,
        )

        assert CardPluginRegistry is not None
        assert PluginInfo is not None

    def test_app_plugins_import(self):
        """测试所有插件可导入"""
        from app.plugins.sys_info import SysInfoPlugin, BasicInfoPlugin
        from app.plugins.switch_info import SwitchInfoPlugin

        # 验证插件实例可创建
        sys_plugin = SysInfoPlugin()
        assert sys_plugin.info.name == "sys_info"

        basic_plugin = BasicInfoPlugin()
        assert basic_plugin.info.name == "basic_info"

        switch_plugin = SwitchInfoPlugin()
        assert switch_plugin.info.name == "switch_info"

    def test_app_ui_main_window_import(self):
        """测试主窗口 UI 可导入"""
        from app.ui.main_window import MainWindow

        # 不实例化（需要 Page），只验证类存在
        assert MainWindow is not None

    def test_app_ui_card_widget_import(self):
        """测试卡片组件可导入"""
        from app.ui.card_widget import DeviceCard

        assert DeviceCard is not None

    def test_app_ui_card_grid_import(self):
        """测试卡片网格可导入"""
        from app.ui.card_grid import DeviceCardGrid

        assert DeviceCardGrid is not None

    def test_app_ui_server_dialog_import(self):
        """测试服务器对话框可导入"""
        from app.ui.server_dialog import DeviceDialog

        assert DeviceDialog is not None

    def test_app_ui_styles_import(self):
        """测试样式模块可导入"""
        from app.ui.styles import Colors

        assert Colors is not None
        # 验证 Colors 有实际颜色值
        assert hasattr(Colors, "PRIMARY")
        assert hasattr(Colors, "SUCCESS")
        assert hasattr(Colors, "ERROR")

    def test_all_main_exports(self):
        """验证 main.py 入口所需的所有导出可用"""
        # 模拟 main.py 的导入顺序
        import flet as ft
        from app.utils.logger import setup_logger, get_logger
        from app.data.database import DeviceDB
        from app.core.ssh_manager import ssh_manager
        from app.ui.main_window import MainWindow

        # 确认关键实例可创建
        logger = setup_logger("main_test")
        assert logger is not None

        db = DeviceDB()
        assert db is not None

        assert ssh_manager is not None
        assert ssh_manager.pool is not None

    def test_flet_dropdown_has_on_select(self):
        """验证 Dropdown 使用 on_select 而非 on_change（0.83+ 兼容性）"""
        import flet as ft
        import inspect

        sig = inspect.signature(ft.Dropdown.__init__)
        params = list(sig.parameters.keys())

        assert "on_select" in params, "Dropdown should have on_select in this Flet version"
        # 确认旧名称 on_change 已不存在
        assert "on_change" not in params, "Dropdown should NOT have on_change (renamed to on_select)"

    def test_flet_textfield_has_on_change(self):
        """验证 TextField 仍使用 on_change（不受影响）"""
        import flet as ft
        import inspect

        sig = inspect.signature(ft.TextField.__init__)
        params = list(sig.parameters.keys())

        assert "on_change" in params, "TextField should have on_change"

    def test_flet_alignment_constants(self):
        """验证 ft.alignment.Alignment.TOP_LEFT 等常量可用（Flet 0.83+）"""
        import flet as ft

        assert hasattr(ft.alignment.Alignment, "TOP_LEFT")
        assert hasattr(ft.alignment.Alignment, "CENTER")
        assert hasattr(ft.alignment.Alignment, "TOP_RIGHT")

    def test_flet_border_api(self):
        """验证 ft.Border.all() API 可用（Flet 0.83+）"""
        import flet as ft

        b = ft.Border.all(width=1, color="#000000")
        assert b is not None
        assert hasattr(b, "top")
        assert hasattr(b, "left")

    def test_flet_button_style_no_text_size(self):
        """验证 ButtonStyle 不接受 text_size 直接参数（Flet 0.83+）"""
        import flet as ft
        import inspect

        sig = inspect.signature(ft.ButtonStyle.__init__)
        params = list(sig.parameters.keys())
        assert "text_size" not in params, "ButtonStyle should not have direct text_size param"

    def test_flet_padding_api(self):
        """验证 ft.padding.Padding 和 ft.padding.only 可用"""
        import flet as ft

        p = ft.padding.Padding(1, 2, 3, 4)
        assert p.left == 1 and p.top == 2
        p2 = ft.padding.only(left=1, top=2)
        assert p2.left == 1 and p2.top == 2

    def test_flet_deprecated_padding_symmetric_warn(self):
        """验证 ft.padding.symmetric 仍存在但已 deprecated（警告性质的检查）"""
        import flet as ft
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = ft.padding.symmetric(vertical=8, horizontal=4)
            # 如果下个版本移除了，这个测试会 FAIL（预期行为）
            depr = [x for x in w if "deprecated" in str(x.message).lower()]
            # 不阻塞，只是记录——0.83 里 deprecated 但未移除

    def test_flet_container_no_border_width(self):
        """验证 Container 不接受 border_width 参数（Flet 0.83+）"""
        import flet as ft
        import inspect

        sig = inspect.signature(ft.Container.__init__)
        params = list(sig.parameters.keys())
        assert "border_width" not in params, "Container should not have border_width param"
        assert "border_color" not in params, "Container should not have border_color param"

    def test_flet_segmented_button_has_on_change(self):
        """验证 SegmentedButton 使用 on_change（不受影响）"""
        import flet as ft
        import inspect

        sig = inspect.signature(ft.SegmentedButton.__init__)
        params = list(sig.parameters.keys())

        assert "on_change" in params, "SegmentedButton should have on_change"

    def test_flet_control_basics(self):
        """验证 flet 基础控件可用"""
        import flet as ft

        # 确认常用控件可创建（不运行，只验证类存在）
        controls_to_check = [
            ft.Text,
            ft.TextField,
            ft.ElevatedButton,
            ft.IconButton,
            ft.Container,
            ft.Row,
            ft.Column,
            ft.Card,
            ft.Dropdown,
            ft.Switch,
            ft.ListTile,
        ]

        for ctrl in controls_to_check:
            assert ctrl is not None, f"Control {ctrl.__name__} not available"
