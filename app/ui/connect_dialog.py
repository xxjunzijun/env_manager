"""
app/ui/connect_dialog.py - 快速连接对话框

简化版添加设备流程：
1. 输入 IP/端口/用户名/密码
2. 点击"连接" → 测试 SSH → 自动获取 hostname
3. 连接成功 → 保存设备 → 对话框关闭 → 卡片出现
"""

import flet as ft
import json
import asyncio
from typing import Callable
from concurrent.futures import ThreadPoolExecutor
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
        self._executor = ThreadPoolExecutor(max_workers=1)

        # 状态 Refs
        self.status_ref = ft.Ref[ft.Text]()
        self.progress_ref = ft.Ref[ft.ProgressBar]()
        self.connect_btn_ref = ft.Ref[ft.Button]()

        # ---- 字段定义 ----
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
            on_submit=lambda e: self._do_connect(),
        )

        # 类型选择器
        self.type_segmented = ft.SegmentedButton(
            segments=[
                ft.Segment(value="server", label=ft.Text("[SVR] 服务器")),
                ft.Segment(value="switch", label=ft.Text("[SW] 交换机")),
                ft.Segment(value="demo", label=ft.Text("[DEMO] 演示")),
            ],
            selected=["server"],
            on_change=self._on_type_change,
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
                ft.Button(
                    "连接",
                    ref=self.connect_btn_ref,
                    on_click=lambda e: self._do_connect(),
                    style=BUTTON_STYLE,
                    icon=ft.icons.Icons.POWER_SETTINGS_NEW,
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

        async def _focus():
            await self.ip_field.focus()

        self._page.run_task(_focus)
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
        self._do_connect()

    def _handle_cancel(self, e=None):
        self.hide()

    # ---- 连接核心逻辑 ----

    def _do_connect(self):
        """点击连接或密码框回车时触发"""
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

        # 提取参数
        host = self.ip_field.value.strip()
        port = int(self.port_field.value or 22)
        username = self.username_field.value.strip()
        password = self.password_field.value or ""
        device_type = list(self.type_segmented.selected)[0]

        self.status_ref.current.value = "正在连接..."
        self.status_ref.current.color = Colors.INFO
        self.progress_bar.visible = True
        self.connect_btn_ref.current.disabled = True
        self.update()
        logger.info(f"连接设备: {username}@{host}:{port}")

        # 用 run_task 执行 SSH 线程任务，完成后切回主线程更新 UI
        self._page.run_task(
            self._async_connect, host, port, username, password, device_type
        )

    async def _async_connect(self, host: str, port: int, username: str,
                              password: str, device_type: str):
        """异步连接任务（SSH 执行在线程池，不阻塞事件循环）"""
        loop = asyncio.get_event_loop()

        try:
            is_online, ext_info, result = await loop.run_in_executor(
                self._executor,
                self._ssh_connect, host, port, username, password, device_type
            )
        except Exception as ex:
            logger.error(f"连接异常: {host}:{port} - {ex}")
            self.status_ref.current.value = f"[X] 连接失败: {ex}"
            self.status_ref.current.color = Colors.ERROR
            self.progress_bar.visible = False
            self.connect_btn_ref.current.disabled = False
            self.update()
            return

        if is_online and result:
            self.status_ref.current.value = "[OK] 连接成功！"
            self.status_ref.current.color = Colors.SUCCESS
            self.progress_bar.visible = False
            self.connect_btn_ref.current.disabled = False
            self.update()

            # 延迟 700ms 关闭，让用户看到成功状态
            await asyncio.sleep(0.7)
            self.hide()
            if self.on_connected:
                self.on_connected(result)
        else:
            msg = result if isinstance(result, str) else "获取设备信息失败"
            self.status_ref.current.value = f"[X] {msg}"
            self.status_ref.current.color = Colors.ERROR
            self.progress_bar.visible = False
            self.connect_btn_ref.current.disabled = False
            self.update()

    def _ssh_connect(self, host: str, port: int, username: str,
                      password: str, device_type: str):
        """SSH 连接 + 插件数据获取（在线程池中执行）"""
        conn = ssh_manager.connect(
            host=host, port=port,
            username=username,
            password=password if password else None,
            ssh_key_path=None,
        )
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
            is_online=True,
            ext_info=ext_info_json,
        )
        return (True, ext_info_json, result)
