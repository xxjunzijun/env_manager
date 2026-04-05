"""
app/ui/card_widget.py - 设备卡片组件

每个服务器/交换机显示为一个卡片
点击卡片打开编辑对话框
"""

import flet as ft
from typing import Callable, Optional
from app.data.models import Device
from app.ui.styles import (
    Colors, CARD_STYLE, CARD_HOVER_STYLE,
    get_status_color
)
from app.utils.logger import get_logger

logger = get_logger("ui.events")


def _build_card_content(device: Device, on_refresh, on_edit):
    """构建设备卡片内容（简化版：只显示 IP、用户名、标签）"""
    type_icons = {"server": "[SVR]", "switch": "[SW]", "demo": "[DEMO]"}
    icon = type_icons.get(device.device_type, "[DEV]")
    status_color = get_status_color(device.is_online)
    status_text = "在线" if device.is_online else "离线"

    # 标签展示
    tags = device.tags_list
    tags_display = ""
    if tags:
        # 只显示前3个标签
        display_tags = tags[:3]
        tags_display = " ".join([f"[{t}]" for t in display_tags])
        if len(tags) > 3:
            tags_display += f" +{len(tags) - 3}"

    content = ft.Column(
        [
            # 头部：图标、名称、状态
            ft.Row(
                [
                    ft.Text(icon, size=20),
                    ft.Column(
                        [
                            ft.Text(
                                device.name,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                device.display_type,
                                size=11,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    ft.Container(
                        content=ft.Text(status_text, size=10, color=status_color),
                        bgcolor=Colors.with_opacity(status_color, 0.12),
                        border_radius=4,
                        padding=ft.Padding(4, 2, 4, 2),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            ft.Divider(height=6, color=Colors.BORDER),
            
            # IP 地址
            ft.Row(
                [
                    ft.Text("📍", size=12),
                    ft.Text(
                        f"{device.ip_address}:{device.port}",
                        size=12,
                        color=Colors.TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
            ),
            
            # 用户名
            ft.Text(
                f"用户: {device.username}",
                size=11,
                color=Colors.TEXT_SECONDARY,
            ),
            
            # 密码（默认隐藏）
            ft.Row(
                [
                    ft.Text("🔑", size=12),
                    ft.Text(
                        "••••••",
                        size=12,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
            ),
            
            # 标签
            ft.Container(
                content=ft.Text(
                    tags_display,
                    size=10,
                    color=Colors.PRIMARY,
                ),
                padding=ft.Padding(0, 4, 0, 0),
            ) if tags_display else ft.Container(),
            
            ft.Container(expand=True),
            
            # 底部按钮
            ft.Row(
                [
                    ft.TextButton(
                        "刷新",
                        icon="refresh",
                        on_click=on_refresh,
                        style=ft.ButtonStyle(
                            icon_size=14,
                            text_style=ft.TextStyle(size=12),
                        ),
                    ),
                    ft.TextButton(
                        "编辑",
                        icon="edit",
                        on_click=on_edit,
                        style=ft.ButtonStyle(
                            icon_size=14,
                            text_style=ft.TextStyle(size=12),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        spacing=3,
    )
    return content


class DeviceCard(ft.Container):
    """
    设备卡片组件

    显示设备信息，支持点击编辑
    """

    def __init__(
        self,
        device: Device,
        on_click: Callable[[Device], None] = None,
        on_refresh: Callable[[Device], None] = None,
        **kwargs
    ):
        self.device = device
        self._user_on_click = on_click
        self._user_on_refresh = on_refresh
        self._hovered = False

        content = _build_card_content(device, self._handle_refresh, self._handle_click)

        # Demo 设备特殊样式
        if device.is_demo:
            style = dict(CARD_STYLE)
            style["border"] = ft.Border.all(
                width=2,
                color=Colors.PRIMARY,
            )
            super().__init__(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text("[示例]", size=11,
                                            color=Colors.PRIMARY,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                ],
                            ),
                            bgcolor=Colors.PRIMARY_LIGHT,
                            padding=ft.Padding(4, 4, 4, 4),
                            border_radius=ft.BorderRadius.only(
                                top_left=12, top_right=12,
                            ),
                        ),
                        ft.Container(
                            content=content,
                            padding=12,
                        ),
                    ],
                    spacing=0,
                ),
                **style,
                on_click=self._handle_click,
                on_hover=self._handle_hover,
            )
        else:
            super().__init__(
                content=content,
                **CARD_STYLE,
                on_click=self._handle_click,
                on_hover=self._handle_hover,
            )

    def _handle_click(self, e):
        logger.debug(f"DeviceCard clicked: {self.device.name}")
        if self._user_on_click:
            self._user_on_click(self.device)

    def _handle_refresh(self, e):
        logger.debug(f"DeviceCard refresh clicked: {self.device.name}")
        if self._user_on_refresh:
            self._user_on_refresh(self.device)

    def _handle_hover(self, e):
        self._hovered = e.data == "true"
        if self._hovered:
            self.border = ft.Border.all(width=1, color=Colors.PRIMARY)
            self.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color="#2196F320",
            )
        else:
            self.border = ft.Border.all(width=1, color=Colors.BORDER)
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color="#00000010",
            )
        self.update()

    def update_device(self, device: Device):
        """更新设备信息"""
        self.device = device
        self.update()


class AddDeviceCard(ft.Container):
    """
    添加设备卡片
    
    点击创建新设备。
    GridView 里的 Container.on_click 在 Flet 0.83 可能被拦截，
    改用 on_click_handler 自定义点击区域解决。
    """

    def __init__(self, on_click: Callable = None):
        self._user_on_click = on_click

        super().__init__(
            content=ft.Column(
                [
                    ft.Text("[+]", size=32),
                    ft.Text("添加设备", size=14, color=Colors.TEXT_SECONDARY),
                    ft.Text("服务器 / 交换机", size=11, color=Colors.TEXT_DISABLED),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            width=220,
            height=200,
            border_radius=12,
            border=ft.Border.all(width=2, color=Colors.BORDER),
            bgcolor=Colors.CARD_BG,
            on_click=self._handle_click,
        )
    
    def _handle_click(self, e):
        logger.debug(f"AddDeviceCard clicked, _user_on_click={bool(self._user_on_click)}")
        if self._user_on_click:
            self._user_on_click()
        else:
            logger.warning("AddDeviceCard clicked but _user_on_click is None")
