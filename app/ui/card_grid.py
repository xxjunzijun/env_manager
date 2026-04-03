"""
app/ui/card_grid.py - 卡片网格布局

设备卡片网格容器，支持添加/删除/刷新卡片
"""

import flet as ft
from typing import List, Callable
from app.data.models import Device
from app.ui.card_widget import DeviceCard, AddDeviceCard
from app.ui.styles import Colors


class DeviceCardGrid(ft.Container):
    """
    设备卡片网格容器
    
    自动排列设备卡片，添加按钮卡片放在网格最后
    """
    
    def __init__(
        self,
        devices: List[Device] = None,
        on_card_click: Callable[[Device], None] = None,
        on_card_refresh: Callable[[Device], None] = None,
        on_add_click: Callable = None,
        **kwargs
    ):
        self.devices = devices or []
        self.on_card_click = on_card_click
        self.on_card_refresh = on_card_refresh
        self.on_add_click = on_add_click
        
        # 卡片网格
        self.grid = ft.GridView(
            expand=True,
            runs_count=4,  # 默认每行4个
            max_extent=230,  # 卡片最大宽度
            spacing=16,
            padding=16,
            child_aspect_ratio=1.0,  # 卡片宽高比
            auto_scroll=True,
        )
        
        # 添加设备卡片（放在 GridView 内部，与设备卡片平级，位于最后）
        self.add_card = AddDeviceCard(on_click=on_add_click) if on_add_click else None
        
        super().__init__(
            content=self.grid,
            expand=True,
            bgcolor=Colors.BG,
        )
        
        self._rebuild_grid()
    
    def set_devices(self, devices: List[Device]):
        """设置设备列表"""
        self.devices = devices
        self._rebuild_grid()
    
    def _rebuild_grid(self):
        """重建卡片网格"""
        self.grid.controls.clear()
        
        # 添加设备卡片
        for device in self.devices:
            card = DeviceCard(
                device=device,
                on_click=self.on_card_click,
                on_refresh=self.on_card_refresh,
            )
            self.grid.controls.append(card)
        
        # 添加设备按钮卡片放在最后
        if self.add_card:
            self.grid.controls.append(self.add_card)


class DeviceListView(ft.ListView):
    """
    设备列表视图（替代网格视图）
    
    适合大量设备的显示，添加按钮卡片放在最后
    """
    
    def __init__(
        self,
        devices: List[Device] = None,
        on_card_click: Callable[[Device], None] = None,
        on_card_refresh: Callable[[Device], None] = None,
        on_add_click: Callable = None,
        **kwargs
    ):
        self.devices = devices or []
        self.on_card_click = on_card_click
        self.on_card_refresh = on_card_refresh
        self.on_add_click = on_add_click
        
        # 添加设备按钮卡片（放在 ListView 最后）
        self.add_card = AddDeviceCard(on_click=on_add_click) if on_add_click else None
        
        super().__init__(
            expand=True,
            spacing=8,
            padding=16,
        )
        
        self._rebuild_list()
    
    def set_devices(self, devices: List[Device]):
        """设置设备列表"""
        self.devices = devices
        self._rebuild_list()
    
    def _rebuild_list(self):
        """重建列表"""
        self.controls.clear()
        
        for device in self.devices:
            card = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "[SVR]" if device.device_type == "server" else "[SW]",
                            size=24,
                        ),
                        ft.Column(
                            [
                                ft.Text(device.name, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    f"{device.ip_address}:{device.port} | {device.username}",
                                    size=12,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "[*] 在线" if device.is_online else "[X] 离线",
                                size=12,
                                color=Colors.SUCCESS if device.is_online else Colors.ERROR,
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.icons.Icons.REFRESH,
                            on_click=lambda e, d=device: self.on_card_refresh and self.on_card_refresh(d),
                        ),
                        ft.IconButton(
                            icon=ft.icons.Icons.EDIT,
                            on_click=lambda e, d=device: self.on_card_click and self.on_card_click(d),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                bgcolor=Colors.CARD_BG,
                border_radius=8,
                padding=12,
            )
            self.controls.append(card)
        
        # 添加设备按钮卡片放在最后
        if self.add_card:
            self.add_card.width = None  # ListView 下不限制宽度
            self.controls.append(self.add_card)
