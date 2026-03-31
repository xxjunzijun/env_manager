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
    get_device_type_color, get_status_color
)


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
        
        # 设备类型图标
        type_icons = {"server": "[SVR]", "switch": "[SW]"}
        icon = type_icons.get(device.device_type, "[DEV]")
        
        # 状态指示器
        status_color = get_status_color(device.is_online)
        status_text = "在线" if device.is_online else "离线"
        
        # 创建卡片内容
        content = ft.Column(
            [
                # 头部：图标 + 名称 + 状态
                ft.Row(
                    [
                        ft.Text(icon, size=24),
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
                        # 状态指示点
                        ft.Container(
                            content=ft.Text(status_text, size=10, color=status_color),
                            bgcolor=f"{status_color}20",
                            border_radius=4,
                            padding=ft.padding.Padding(4, 2, 4, 2),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                
                ft.Divider(height=8, color=Colors.BORDER),
                
                # IP 和端口
                ft.Row(
                    [
                        ft.Text("📍", size=12),
                        ft.Text(
                            f"{device.ip_address}:{device.port}",
                            size=12,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                ),
                
                ft.Text(
                    f"用户: {device.username}",
                    size=11,
                    color=Colors.TEXT_SECONDARY,
                ),
                
                # 扩展信息区域（动态内容）
                ft.Container(
                    content=ft.Column([], spacing=2),
                    expand=True,
                    alignment=ft.alignment.Alignment.TOP_LEFT,
                ),
                
                # 底部操作按钮
                ft.Row(
                    [
                        ft.TextButton(
                            "刷新",
                            icon="refresh",
                            on_click=self._handle_refresh,
                            style=ft.ButtonStyle(
                                icon_size=14,
                                text_style=ft.TextStyle(size=12),
                            ),
                        ),
                        ft.TextButton(
                            "编辑",
                            icon="edit",
                            on_click=self._handle_click,
                            style=ft.ButtonStyle(
                                icon_size=14,
                                text_style=ft.TextStyle(size=12),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=4,
        )
        
        super().__init__(
            content=content,
            **CARD_STYLE,
            on_click=self._handle_click,
            on_hover=self._handle_hover,
        )
    
    def _handle_click(self, e):
        if self._user_on_click:
            self._user_on_click(self.device)

    def _handle_refresh(self, e):
        if self._user_on_refresh:
            self._user_on_refresh(self.device)
        e.stop_propagation()
    
    def _handle_hover(self, e):
        self._hovered = e.data == "true"
        if self._hovered:
            self.border_color = Colors.PRIMARY
            self.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color="#2196F320",
            )
        else:
            self.border_color = Colors.BORDER
            self.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color="#00000010",
            )
        self.update()
    
    def update_device(self, device: Device):
        """更新设备信息"""
        self.device = device
        # 重新渲染卡片
        self.update()


class AddDeviceCard(ft.Container):
    """
    添加设备卡片
    
    点击创建新设备
    """
    
    def __init__(self, on_click: Callable = None):
        self._user_on_click = on_click

        content = ft.Column(
            [
                ft.Text("[+]", size=32),
                ft.Text("添加设备", size=14, color=Colors.TEXT_SECONDARY),
                ft.Text("服务器 / 交换机", size=11, color=Colors.TEXT_DISABLED),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        super().__init__(
            content=content,
            width=220,
            height=200,
            border_radius=12,
            border=ft.Border.all(width=2, color=Colors.BORDER),
            bgcolor=Colors.CARD_BG,
            on_click=self._handle_click,
        )
    
    def _handle_click(self, e):
        if self._user_on_click:
            self._user_on_click()
