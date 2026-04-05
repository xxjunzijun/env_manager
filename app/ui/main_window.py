"""
app/ui/main_window.py - 主窗口

应用程序主界面
"""

import flet as ft
import json
from typing import List
from app.data.models import Device
from app.data.database import DeviceDB
from app.ui.card_widget import DeviceCard, AddDeviceCard
from app.ui.card_grid import DeviceCardGrid, DeviceListView
from app.ui.server_dialog import DeviceDialog
from app.ui.connect_dialog import ConnectDialog
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

    def _show_snack_bar(self, message: str):
        """显示 SnackBar 消息

        Flet 0.83.1 使用 page.overlay 配合 SnackBar 替代已废弃的 page.show_snack_bar()
        """
        snackbar = ft.SnackBar(content=ft.Text(message))
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _setup_page(self):
        """设置页面"""
        logger.debug("设置页面属性...")
        self.page.title = "[SVR] Server Manager - 服务器/交换机管理"
        self.page.theme_mode = ft.ThemeMode.DARK  # 深色主题
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.padding = 0
        logger.debug("页面属性设置完成: title=Server Manager, size=1200x800, theme=dark")
        self.page.theme = ft.Theme(
            color_scheme_seed=Colors.PRIMARY,
            brightness=ft.Brightness.DARK,
        )

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
            on_select=self._on_filter_change,
            width=120,
        )

        self.group_filter = ft.Dropdown(
            hint_text="分组",
            options=[ft.dropdown.Option("all", "全部分组")],
            value="all",
            on_select=self._on_filter_change,
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
            padding=ft.Padding(12, 8, 12, 8),
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
            on_reorder=self._handle_reorder,
        )

        # 对话框引用（ConnectDialog 用于添加，DeviceDialog 用于编辑）
        self._add_dialog: ConnectDialog = None
        self._edit_dialog: DeviceDialog = None

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
                    ),
                ],
            ),
            bgcolor=Colors.CARD_BG,
            padding=ft.Padding(12, 8, 12, 8),
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

    def run(self):
        """运行应用"""
        self.page.update()

    def _load_devices(self):
        """加载设备列表"""
        self.devices = self.db.get_all_devices()

        # 如果数据库为空，插入示例设备
        if not self.devices:
            self._ensure_demo_device()
            self.devices = self.db.get_all_devices()

        self._update_group_filter()
        self._update_device_view()
        self._update_status()

    def _ensure_demo_device(self):
        """确保存在一个示例设备"""
        import json
        demo_data = json.dumps({
            "hostname": "demo-server-01",
            "sysname": "Linux",
            "os": "Ubuntu 22.04 LTS",
            "cpu_count": "4",
            "memory_total": "8 GB",
        })
        demo = Device(
            name="Demo 服务器",
            device_type="server",
            ip_address="192.168.1.100",
            port=22,
            username="root",
            password="demo",
            group="示例环境",
            tags="示例,演示",
            description="这是示例设备，仅供演示",
            is_online=True,
            ext_info=demo_data,
            is_demo=True,
        )
        try:
            self.db.add_device(demo)
            logger.info("示例设备已创建")
        except Exception as e:
            logger.error(f"创建示例设备失败: {e}")

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
        logger.debug(f"搜索事件: e={e}, control={getattr(e, 'control', None)}")
        self._update_device_view()
        self._update_status()

    def _on_filter_change(self, e):
        """过滤变更"""
        logger.debug(f"过滤变更事件: e={e}, control={getattr(e, 'control', None)}")
        self._update_device_view()
        self._update_status()

    def _toggle_view(self, e):
        """切换视图"""
        logger.debug(f"切换视图: _is_grid_view={self._is_grid_view}")
        self._is_grid_view = not self._is_grid_view
        self.view_toggle.icon = (
            ft.icons.Icons.VIEW_LIST if self._is_grid_view else ft.icons.Icons.GRID_VIEW
        )
        self._update_device_view()

    def _handle_reorder(self, devices: List[Device]):
        """处理卡片拖拽排序"""
        logger.info(f"卡片排序更新: 共 {len(devices)} 台设备")
        try:
            # 更新每台设备的 display_order
            for order, device in enumerate(devices):
                self.db.update_device(device.id, display_order=order)
            logger.info("设备排序已保存")
        except Exception as e:
            logger.error(f"保存设备排序失败: {e}")

    def _show_add_dialog(self, e=None):
        """显示添加设备对话框（快速连接流程）"""
        logger.debug("打开添加设备对话框")
        try:
            if self._add_dialog is None:
                self._add_dialog = ConnectDialog(
                    page=self.page,
                    on_connected=self._handle_new_device_connected,
                )
                logger.debug("ConnectDialog 实例创建成功")
            self._add_dialog.show()
            logger.debug("添加设备对话框已显示")
        except Exception as ex:
            logger.error(f"显示添加对话框失败: {ex}", exc_info=True)

    def _is_ip_duplicate(self, ip_address: str, exclude_id: int = None) -> bool:
        """检查 IP 地址是否已被其他设备使用"""
        all_devices = self.db.get_all_devices()
        for d in all_devices:
            if d.ip_address == ip_address and (exclude_id is None or d.id != exclude_id):
                return True
        return False

    def _handle_new_device_connected(self, device: Device):
        """新设备连接成功后保存"""
        logger.info(f"新设备连接成功: name={device.name}, ip={device.ip_address}")
        if self._is_ip_duplicate(device.ip_address):
            self._show_snack_bar(f"IP {device.ip_address} 已存在，请勿重复添加")
            return
        try:
            device_id = self.db.add_device(device)
            device.id = device_id
            logger.info(f"设备添加完成: id={device_id}, name={device.name}")
            self._load_devices()
            self._show_snack_bar(f"{device.name} 添加成功")
        except Exception as e:
            logger.error(f"保存新设备异常: {e}")
            self._show_snack_bar(f"添加失败: {e}")

    def _show_edit_dialog(self, device: Device):
        """显示编辑设备对话框"""
        logger.debug(f"打开编辑设备对话框: id={device.id}, name={device.name}")
        # 示例设备不允许编辑
        if device.is_demo:
            self._show_snack_bar("这是示例设备，无法编辑")
            return
        try:
            self._edit_dialog = DeviceDialog(
                page=self.page,
                device=device,
                on_save=self._handle_save_device,
                on_delete=self._handle_delete_device,
            )
            self._edit_dialog.show()
            logger.debug("编辑设备对话框已显示")
        except Exception as ex:
            logger.error(f"显示编辑对话框失败: {ex}", exc_info=True)

    def _handle_save_device(self, device: Device):
        """保存设备"""
        logger.info(f"保存设备: name={device.name}, type={device.device_type}")
        if self._is_ip_duplicate(device.ip_address, exclude_id=device.id):
            self._show_snack_bar(f"IP {device.ip_address} 已被其他设备使用")
            return
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
            self._show_snack_bar(f"保存失败: {e}")

    def _handle_delete_device(self, device_id: int):
        """删除设备（示例设备不允许删除）"""
        logger.info(f"删除设备: id={device_id}")
        try:
            # 禁止删除示例设备
            device = self.db.get_device(device_id)
            if device and device.is_demo:
                self._show_snack_bar("示例设备无法删除")
                return
            self.db.delete_device(device_id)
            logger.info(f"设备删除完成: id={device_id}")
            self._load_devices()
        except Exception as e:
            logger.error(f"删除设备异常: {e}")
            self._show_snack_bar(f"删除失败: {e}")

    def _refresh_device(self, device: Device):
        """刷新设备信息"""
        import threading
        import json
        from datetime import datetime

        # 提取 primitives：避免闭包捕获 self（含 Flet 控件）进 call_later
        device_id = device.id
        device_name = device.name
        host = device.ip_address
        port = device.port
        username = device.username
        password = device.password
        ssh_key_path = device.ssh_key_path
        device_type = device.device_type

        # 判断是否为 demo 模式：device_type 为 "demo" 或名称含 "demo"
        is_demo_mode = device_type == "demo" or "demo" in device_name.lower()
        if is_demo_mode:
            logger.info(f"Demo 模式设备，使用 StubPlugin: {device_name}")

        logger.info(f"刷新设备任务启动: id={device_id}, name={device_name}, ip={host}, is_demo={is_demo_mode}")

        def do_refresh():
            try:
                # 获取该设备类型对应的插件
                plugins = CardPluginRegistry.get_plugins_for_type(device_type)
                logger.debug(f"找到 {len(plugins)} 个插件: {[p.info.name for p in plugins]}")

                # 合并所有插件数据
                all_data = {}
                
                if is_demo_mode:
                    # Demo 模式：使用 StubPlugin，不进行真实 SSH 连接
                    stub_plugin = CardPluginRegistry.get_plugin("stub")
                    if stub_plugin:
                        try:
                            logger.debug("执行 StubPlugin 获取模拟数据")
                            data = stub_plugin.fetch(None)  # ssh_conn 参数被忽略
                            all_data.update(data)
                        except Exception as e:
                            logger.error(f"StubPlugin 执行失败: {e}")
                else:
                    # 真实模式：通过 SSH 获取数据
                    logger.debug(f"开始 SSH 连接: {host}:{port}")

                    # 获取 SSH 连接
                    conn = ssh_manager.connect(
                        host=host, port=port,
                        username=username,
                        password=password,
                        ssh_key_path=ssh_key_path,
                    )

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
                    device_id,
                    is_online=True,
                    last_check=datetime.now(),
                    ext_info=json.dumps(all_data),
                )

                # 更新 UI - 从线程安全调用
                def update_ui():
                    self._load_devices()
                    mode_str = "[Demo] " if is_demo_mode else ""
                    self._show_snack_bar(f"{mode_str}{device_name} 刷新成功")

                self.page.loop.call_later(0, update_ui)
                logger.info(f"设备刷新成功: {device_name}")

            except Exception as e:
                logger.error(f"刷新设备失败: id={device_id}, name={device_name}, error={e}")

                # 更新离线状态
                self.db.update_device(device_id, is_online=False)

                def update_ui():
                    self._load_devices()
                    self._show_snack_bar(f"{device_name} 刷新失败: {e}")

                self.page.loop.call_later(0, update_ui)

        threading.Thread(target=do_refresh, daemon=True).start()
