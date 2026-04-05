"""
app/ui/card_grid.py - 卡片网格布局

设备卡片网格容器，支持添加/删除/刷新卡片
支持拖拽排序
"""

import flet as ft
from typing import List, Callable, Optional
from app.data.models import Device
from app.ui.card_widget import DeviceCard, AddDeviceCard
from app.ui.styles import Colors
from app.utils.logger import get_logger

logger = get_logger("ui.cardgrid")


class DeviceCardGrid(ft.Container):
    """
    设备卡片网格容器
    
    自动排列设备卡片，添加按钮卡片放在网格最后
    支持拖拽排序
    """
    
    def __init__(
        self,
        devices: List[Device] = None,
        on_card_click: Callable[[Device], None] = None,
        on_card_refresh: Callable[[Device], None] = None,
        on_add_click: Callable = None,
        on_reorder: Callable[[List[Device]], None] = None,
        **kwargs
    ):
        self.devices = devices or []
        self.on_card_click = on_card_click
        self.on_card_refresh = on_card_refresh
        self.on_add_click = on_add_click
        self.on_reorder = on_reorder
        
        # 拖拽状态
        self._drag_source_index: Optional[int] = None
        self._drag_target_index: Optional[int] = None
        
        # 卡片网格 - 使用 wrap 模式以便支持拖拽
        self.grid = ft.Wrap(
            spacing=16,
            run_spacing=16,
            alignment=ft.WrapAlignment.START,
        )
        
        # 添加设备卡片
        self.add_card = AddDeviceCard(on_click=on_add_click) if on_add_click else None
        
        super().__init__(
            content=ft.Column(
                [self.grid],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
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
        for i, device in enumerate(self.devices):
            card = DeviceCard(
                device=device,
                on_click=self.on_card_click,
                on_refresh=self.on_card_refresh,
            )
            # 设置拖拽属性
            card.draggable = True
            card.on_drag_start = lambda e, idx=i: self._handle_drag_start(e, idx)
            card.on_drag_end = lambda e: self._handle_drag_end(e)
            card.data = i  # 存储索引
            
            # 拖放目标处理
            card.on_drag_enter = lambda e, idx=i: self._handle_drag_enter(e, idx)
            card.on_drag_over = lambda e: self._handle_drag_over(e)
            card.on_drag_leave = lambda e: self._handle_drag_leave(e)
            card.on_drop = lambda e, idx=i: self._handle_drop(e, idx)
            
            self.grid.controls.append(card)
        
        # 添加设备按钮卡片放在最后
        if self.add_card:
            # 添加按钮卡片不设置拖拽
            self.grid.controls.append(self.add_card)
    
    def _handle_drag_start(self, e: ft.DragStartEvent, index: int):
        """开始拖拽"""
        self._drag_source_index = index
        logger.debug(f"拖拽开始: index={index}")
    
    def _handle_drag_end(self, e: ft.DragEndEvent):
        """结束拖拽"""
        logger.debug(f"拖拽结束")
        self._drag_source_index = None
        self._drag_target_index = None
        # 移除所有高亮
        self._rebuild_grid()
    
    def _handle_drag_enter(self, e: ft.DragTargetEvent, target_index: int):
        """拖拽进入目标"""
        if self._drag_source_index is not None and self._drag_source_index != target_index:
            self._drag_target_index = target_index
            # 高亮目标卡片
            self._highlight_target(target_index)
        e.prevent_default()
    
    def _handle_drag_over(self, e: ft.DragTargetEvent):
        """拖拽经过目标"""
        e.prevent_default()
    
    def _handle_drag_leave(self, e: ft.DragTargetLeaveEvent):
        """拖拽离开目标"""
        pass
    
    def _handle_drop(self, e: ft.DragTargetEvent, target_index: int):
        """放置卡片"""
        e.prevent_default()
        
        if self._drag_source_index is None or self._drag_source_index == target_index:
            return
        
        logger.debug(f"放置: source={self._drag_source_index}, target={target_index}")
        
        # 重新排序设备列表
        devices = self.devices.copy()
        source_device = devices.pop(self._drag_source_index)
        
        # 调整目标索引（如果源在目标之前）
        adjusted_target = target_index
        if self._drag_source_index < target_index:
            adjusted_target = target_index - 1
        
        devices.insert(adjusted_target, source_device)
        self.devices = devices
        
        # 触发重绘
        self._rebuild_grid()
        
        # 持久化新顺序到数据库
        if self.on_reorder:
            self.on_reorder(self.devices)
        
        self._drag_source_index = None
        self._drag_target_index = None
    
    def _highlight_target(self, target_index: int):
        """高亮目标卡片"""
        self._rebuild_grid()
        if 0 <= target_index < len(self.grid.controls):
            target_card = self.grid.controls[target_index]
            if not isinstance(target_card, AddDeviceCard):
                target_card.border = ft.Border.all(width=2, color=Colors.PRIMARY)
                target_card.shadow = ft.BoxShadow(
                    spread_radius=3,
                    blur_radius=12,
                    color="#6366F150",
                )
                target_card.update()


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
