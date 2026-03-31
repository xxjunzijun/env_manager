"""
app/ui/main_window.py - 主窗口

应用程序主界面
"""

import flet as ft
from typing import List
from app.data.models import Device
from app.data.database import DeviceDB
from app.ui.card_widget import DeviceCard, AddDeviceCard
from app.ui.card_grid import DeviceCardGrid, DeviceListView
from app.ui.server_dialog import DeviceDialog
from app.ui.styles import Colors
from app.core.card_plugin import CardPluginRegistry
from app.core.ssh_manager import ssh_manager
from app.utils.logger import get_logger

# 导入插件以自动注册
from app.plugins import sys_info, network_info, switch_info


logger = get_logger("ui.main")


class MainWindow:
    """主窗口"""
    
    def __init__(self, page: ft.Page):
        logger.info("MainWindow 初始化...")
        self.page = page
        self.db = DeviceDB()
        self.devices: List[Device] = []
        
        # 初始化
        self._setup_page()
        self._setup_ui()
        self._load_devices()
        
        # 注册所有插件
        plugins = CardPluginRegistry.list_plugins()
        logger.info(f"已注册插件: {[p.name for p in plugins]}")
        logger.info("MainWindow 初始化完成")
    
    def _setup_page(self):
        """设置页面"""
        logger.debug("设置页面属性...")
        self.page.title = "[SVR] Server Manager - 服务器/交换机管理"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.padding = 0
        logger.debug("页面属性设置完成: title=Server Manager, size=1200x800")
        self.page.styles = {
            "AppBar": {
                "bgcolor": Colors.PRIMARY,
                "color": "white",
            },
            "Card": {
                "bgcolor": Colors.CARD_BG,
            },
        }
    
    def _setup_ui(self):
        """设置 UI"""
        
        # 工具栏
        self.search_field = ft.TextField(
            hint_text="搜索设备...",
            prefix_icon=ft.icons.Icons.SEARCH,
            on_change=self._on_search,
            expand=True,
        )
        
        self.type_filter = ft.Dropdown(
            hint_text="类型",
            options=[
                ft.dropdown.Option("all", "全部"),
                ft.dropdown.Option("server", "服务器"),
                ft.dropdown.Option("switch", "交换机"),
            ],
            value="all",
            on_change=self._on_filter_change,
            width=120,
        )
        
        self.group_filter = ft.Dropdown(
            hint_text="分组",
            options=[ft.dropdown.Option("all", "全部分组")],
            value="all",
            on_change=self._on_filter_change,
            width=140,
        )
        
        self.view_toggle = ft.IconButton(
            icon=ft.icons.Icons.GRID_VIEW,
            tooltip="网格视图",
            on_click=self._toggle_view,
        )
        self._is_grid_view = True
        
        toolbar = ft.Container(
            content=ft.Row(
                [
                    self.search_field,
                    self.type_filter,
                    self.group_filter,
                    self.view_toggle,
                    ft.IconButton(
                        icon=ft.icons.Icons.ADD,
                        tooltip="添加设备",
                        on_click=self._show_add_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            ),
            bgcolor=Colors.CARD_BG,
            padding=ft.padding.Padding(12, 8, 12, 8),
            border=ft.border.Border(
                bottom=ft.border.BorderSide(1, Colors.BORDER)
            ),
        )
        
        # 设备列表/网格
        self.device_view = DeviceCardGrid(
            devices=self.devices,
            on_card_click=self._show_edit_dialog,
            on_card_refresh=self._refresh_device,
            on_add_click=self._show_add_dialog,
        )
        
        # 状态栏
        self.status_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "就绪",
                        size=12,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        "0 台设备",
                        size=12,
                        color=Colors.TEXT_SECONDARY,
                        ref=self._device_count_ref() if hasattr(self, '_device_count_ref') else None,
                    ),
                ],
            ),
            bgcolor=Colors.CARD_BG,
            padding=ft.padding.Padding(12, 8, 12, 8),
            border=ft.border.Border(
                top=ft.border.BorderSide(1, Colors.BORDER)
            ),
        )
        
        # 组装主界面
        self.page.add(
            ft.Column(
                [
                    toolbar,
                    self.device_view,
                    self.status_bar,
                ],
                expand=True,
                spacing=0,
            )
        )
    
    def _device_count_ref(self):
        """设备计数引用"""
        if not hasattr(self, '_device_count_text'):
            self._device_count_text = ft.Ref[ft.Text]()
        return self._device_count_text
    
    def run(self):
        """运行应用"""
        self.page.update()
    
    def _load_devices(self):
        """加载设备列表"""
        self.devices = self.db.get_all_devices()
        self._update_group_filter()
        self._update_device_view()
        self._update_status()
    
    def _update_device_view(self):
        """更新设备视图"""
        filtered = self._get_filtered_devices()
        
        if self._is_grid_view:
            self.device_view.set_devices(filtered)
        else:
            self.device_view.set_devices(filtered)
        
        self.page.update()
    
    def _get_filtered_devices(self) -> List[Device]:
        """获取过滤后的设备列表"""
        filtered = self.devices
        
        # 类型过滤
        type_filter = self.type_filter.value
        if type_filter != "all":
            filtered = [d for d in filtered if d.device_type == type_filter]
        
        # 分组过滤
        group_filter = self.group_filter.value
        if group_filter != "all":
            filtered = [d for d in filtered if d.group == group_filter]
        
        # 搜索过滤
        search = self.search_field.value.lower()
        if search:
            filtered = [
                d for d in filtered
                if search in d.name.lower()
                or search in d.ip_address.lower()
                or search in d.tags.lower()
            ]
        
        return filtered
    
    def _update_group_filter(self):
        """更新分组过滤下拉框"""
        groups = self.db.get_all_groups()
        self.group_filter.options = [
            ft.dropdown.Option("all", "全部分组"),
            *[ft.dropdown.Option(g, g) for g in groups],
        ]
    
    def _update_status(self):
        """更新状态栏"""
        count = len(self._get_filtered_devices())
        total = len(self.devices)
        
        status_text = f"显示 {count}/{total} 台设备"
        self.status_bar.content.controls[0].value = status_text
    
    def _on_search(self, e):
        """搜索"""
        self._update_device_view()
        self._update_status()
    
    def _on_filter_change(self, e):
        """过滤变更"""
        self._update_device_view()
        self._update_status()
    
    def _toggle_view(self, e):
        """切换视图"""
        self._is_grid_view = not self._is_grid_view
        self.view_toggle.icon = (
            ft.icons.Icons.VIEW_LIST if self._is_grid_view else ft.icons.Icons.GRID_VIEW
        )
        self._update_device_view()
    
    def _show_add_dialog(self, e=None):
        """显示添加设备对话框"""
        logger.debug("打开添加设备对话框")
        dialog = DeviceDialog(
            on_save=self._handle_save_device,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_edit_dialog(self, device: Device):
        """显示编辑设备对话框"""
        logger.debug(f"打开编辑设备对话框: id={device.id}, name={device.name}")
        dialog = DeviceDialog(
            device=device,
            on_save=self._handle_save_device,
            on_delete=self._handle_delete_device,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _handle_save_device(self, device: Device):
        """保存设备"""
        logger.info(f"保存设备: name={device.name}, type={device.device_type}")
        try:
            if device.id:
                # 更新
                self.db.update_device(
                    device.id,
                    name=device.name,
                    device_type=device.device_type,
                    ip_address=device.ip_address,
                    port=device.port,
                    username=device.username,
                    password=device.password,
                    ssh_key_path=device.ssh_key_path,
                    group=device.group,
                    tags=device.tags,
                    description=device.description,
                )
                logger.info(f"设备更新完成: id={device.id}, name={device.name}")
            else:
                # 新增
                device_id = self.db.add_device(device)
                device.id = device_id
                logger.info(f"设备添加完成: id={device_id}, name={device.name}")
            
            self._load_devices()
            
        except Exception as e:
            logger.error(f"保存设备异常: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"保存失败: {e}"))
            )
    
    def _handle_delete_device(self, device_id: int):
        """删除设备"""
        logger.info(f"删除设备: id={device_id}")
        try:
            self.db.delete_device(device_id)
            logger.info(f"设备删除完成: id={device_id}")
            self._load_devices()
        except Exception as e:
            logger.error(f"删除设备异常: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"删除失败: {e}"))
            )
    
    def _refresh_device(self, device: Device):
        """刷新设备信息"""
        import threading
        import json
        from datetime import datetime
        
        logger.info(f"刷新设备任务启动: id={device.id}, name={device.name}, ip={device.ip_address}")
        
        def do_refresh():
            try:
                logger.debug(f"开始 SSH 连接: {device.ip_address}:{device.port}")
                
                # 获取 SSH 连接
                conn = ssh_manager.connect(
                    host=device.ip_address,
                    port=device.port,
                    username=device.username,
                    password=device.password,
                    ssh_key_path=device.ssh_key_path,
                )
                
                # 获取该设备类型对应的插件
                plugins = CardPluginRegistry.get_plugins_for_type(device.device_type)
                logger.debug(f"找到 {len(plugins)} 个插件: {[p.info.name for p in plugins]}")
                
                # 合并所有插件数据
                all_data = {}
                for plugin in plugins:
                    try:
                        logger.debug(f"执行插件: {plugin.info.name}")
                        data = plugin.fetch(conn)
                        all_data.update(data)
                    except Exception as e:
                        logger.error(f"插件 {plugin.info.name} 执行失败: {e}")
                
                # 关闭连接
                conn.close()
                logger.debug("SSH 连接已关闭")
                
                # 更新数据库
                self.db.update_device(
                    device.id,
                    is_online=True,
                    last_check=datetime.now(),
                    ext_info=json.dumps(all_data),
                )
                
                # 更新 UI - 使用 call_later 从线程安全更新
                def update_ui():
                    self._load_devices()
                    self.page.show_snack_bar(
                        ft.SnackBar(content=ft.Text(f"{device.name} 刷新成功"))
                    )
                
                self.page.call_later(0, update_ui)
                logger.info(f"设备刷新成功: {device.name}")
                
            except Exception as e:
                logger.error(f"刷新设备失败: id={device.id}, name={device.name}, error={e}")
                
                # 更新离线状态
                self.db.update_device(device.id, is_online=False)
                
                def update_ui():
                    self._load_devices()
                    self.page.show_snack_bar(
                        ft.SnackBar(content=ft.Text(f"{device.name} 刷新失败: {e}"))
                    )
                
                self.page.call_later(0, update_ui)
        
        threading.Thread(target=do_refresh, daemon=True).start()
