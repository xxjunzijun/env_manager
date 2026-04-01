"""
app/ui/connect_dialog.py - 快速连接对话框

简化版添加设备流程：
1. 输入 IP/端口/用户名/密码
2. 点击"连接" → 测试 SSH → 自动获取 hostname
3. 连接成功 → 保存设备 → 对话框关闭 → 卡片出现
"""

import flet as ft
import json
from typing import Callable
from app.data.models import Device
from app.ui.styles import Colors, BUTTON_STYLE
from app.core.ssh_manager import ssh_manager
from app.core.card_plugin import CardPluginRegistry
from app.utils.logger import get_logger


logger = get_logger("ui.dialog")


class ConnectDialog(ft.Container):
    """
    快速连接对话框 - 自定义 Modal Overlay

    简化流程：输入连接信息 → 连接测试 → 保存设备
    """

    def __init__(
        self,
        page: ft.Page,
        on_connected: Callable[[Device], None] = None,
    ):
        self._page = page
        self.on_connected = on_connected

        # 状态 Refs
        self.status_ref = ft.Ref[ft.Text]()
        self.progress_ref = ft.Ref[ft.ProgressBar]()
        self.connect_btn_ref = ft.Ref[ft.ElevatedButton]()

        # 设备类型（默认服务器）
        self.type_segmented = ft.SegmentedButton(
            segments=[
                ft.Segment(value="server", label=ft.Text("[SVR] 服务器")),
                ft.Segment(value="switch", label=ft.Text("[SW] 交换机")),
            ],
            selected={"server"},
            on_change=self._on_type_change,
        )

        # 连接表单
        self.ip_field = ft.TextField(
            label="IP 地址 / 主机名",
            hint_text="如: 192.168.1.100",
            autofocus=True,
            keyboard_type=ft.KeyboardType.URL,
        )
        self.port_field = ft.TextField(
            label="端口",
            hint_text="默认 22",
            value="22",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
        )
        self.username_field = ft.TextField(
            label="用户名",
            hint_text="root",
        )
        self.password_field = ft.TextField(
            label="密码",
            hint_text="••••••",
            password=True,
            can_reveal_password=True,
        )

        self.status_text = ft.Text(
            ref=self.status_ref,
            size=13,
            color=Colors.TEXT_SECONDARY,
        )
        self.progress_bar = ft.ProgressBar(ref=self.progress_ref, visible=False)

        form = ft.Column(
            [
                ft.Text("设备类型", size=12, color=Colors.TEXT_SECONDARY),
                self.type_segmented,
                ft.Container(height=12),
                self.ip_field,
                ft.Row([self.port_field]),
                self.username_field,
                self.password_field,
                ft.Container(height=8),
                self.progress_bar,
                self.status_text,
            ],
            tight=True, spacing=8,
        )

        actions = ft.Row(
            [
                ft.TextButton("取消", on_click=self._handle_cancel),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "连接",
                    ref=self.connect_btn_ref,
                    on_click=self._handle_connect,
                    style=BUTTON_STYLE,
                    icon=ft.icons.Icons.POWER,
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        dialog_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("[+] 连接新设备", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "输入 SSH 连接信息，点击连接后将自动获取设备信息",
                        size=12, color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=12),
                    form,
                    ft.Container(height=12),
                    actions,
                ],
                tight=True, spacing=0,
            ),
            width=400, padding=20,
            bgcolor=Colors.CARD_BG,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=4, blur_radius=20,
                color="#00000040",
            ),
        )

        super().__init__(
            content=ft.Stack(
                [
                    ft.Container(
                        expand=True,
                        bgcolor="#00000080",
                        on_click=self._handle_cancel,
                    ),
                    ft.Container(
                        content=dialog_content,
                        alignment=ft.alignment.Alignment.CENTER,
                    ),
                ],
                width=800, height=600,
            ),
            visible=False,
            width=800, height=600,
        )

    # ---- 生命周期 ----

    def show(self):
        self.visible = True
        if self not in self._page.controls:
            self._page.add(self)
        self._page.update()
        logger.debug("ConnectDialog 已显示")

    def hide(self):
        self.visible = False
        self.ip_field.value = ""
        self.port_field.value = "22"
        self.username_field.value = ""
        self.password_field.value = ""
        self.status_text.value = ""
        self.progress_bar.visible = False
        self._page.update()
        logger.debug("ConnectDialog 已隐藏并重置")

    # ---- 事件处理 ----

    def _on_type_change(self, e):
        self.update()

    def _handle_connect(self, e):
        """连接并保存设备"""
        import threading

        # 验证
        if not self.ip_field.value.strip():
            self.status_ref.current.value = "请输入 IP 地址"
            self.status_ref.current.color = Colors.ERROR
            self.update()
            return
        if not self.username_field.value.strip():
            self.status_ref.current.value = "请输入用户名"
            self.status_ref.current.color = Colors.ERROR
            self.update()
            return

        # 提取 primitives：避免闭包捕获 self
        host = self.ip_field.value.strip()
        port = int(self.port_field.value or 22)
        username = self.username_field.value.strip()
        password = self.password_field.value or ""
        device_type = list(self.type_segmented.selected)[0]
        status_text = self.status_ref.current
        progress_bar = self.progress_ref.current
        connect_btn = self.connect_btn_ref.current
        page = self._page
        on_connected = self.on_connected
        dialog_hide = self.hide
        dialog_update = self.update

        logger.info(f"连接设备: {username}@{host}:{port}")

        progress_bar.visible = True
        status_text.value = "正在连接..."
        status_text.color = Colors.INFO
        connect_btn.disabled = True
        dialog_update()

        def do_connect():
            result = None
            is_online = False
            ext_info = "{}"

            try:
                conn = ssh_manager.connect(
                    host=host, port=port,
                    username=username,
                    password=password if password else None,
                )
                is_online = True

                # 获取设备类型对应的插件信息
                plugins = CardPluginRegistry.get_plugins_for_type(device_type)
                all_data = {}
                for plugin in plugins:
                    try:
                        data = plugin.fetch(conn)
                        all_data.update(data)
                    except Exception as ex:
                        logger.error(f"插件 {plugin.info.name} 执行失败: {ex}")
                ext_info_json = json.dumps(all_data)
                conn.close()

                # 优先用 hostname，否则用 IP
                name = (all_data.get("hostname")
                        or all_data.get("sysname")
                        or host)

                result = Device(
                    name=name,
                    device_type=device_type,
                    ip_address=host,
                    port=port,
                    username=username,
                    password=password if password else None,
                    is_online=is_online,
                    ext_info=ext_info_json,
                )

                def on_success():
                    status_text.value = "[OK] 连接成功！"
                    status_text.color = Colors.SUCCESS
                    connect_btn.disabled = False
                    progress_bar.visible = False
                    dialog_update()
                    # 延迟关闭，给用户看到成功提示
                    page.call_later(700, lambda _: (
                        dialog_hide(),
                        on_connected(result) if on_connected else None
                    ))

                page.call_later(0, on_success)

            except Exception as ex:
                logger.error(f"连接失败: {host}:{port} - {ex}")

                def on_fail():
                    status_text.value = f"[X] 连接失败: {ex}"
                    status_text.color = Colors.ERROR
                    connect_btn.disabled = False
                    progress_bar.visible = False
                    dialog_update()

                page.call_later(0, on_fail)

        threading.Thread(target=do_connect, daemon=True).start()

    def _handle_cancel(self, e=None):
        self.hide()



