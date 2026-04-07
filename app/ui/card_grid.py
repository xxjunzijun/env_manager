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
        
        # 卡片网格 - 使用 Row(wrap=True) + expand 撑满宽度
        self.grid = ft.Row(
            wrap=True,
            spacing=16,
            run_spacing=16,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
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
        
        for i, device in enumerate(self.devices):
            card = DeviceCard(
                device=device,
                on_click=self.on_card_click,
                on_refresh=self.on_card_refresh,
            )
            # Stack: 卡片在底层，DragTarget 透明覆盖层在上层接收拖放事件
            stack = ft.Stack([card], width=220, height=200)
            # 用 Draggable 包装 Stack（draggable 属性在 Container 上无效）
            draggable = ft.Draggable(
                content=stack,
                data=i,
                on_drag_start=lambda e, idx=i: self._handle_drag_start(e, idx),
                on_drag_complete=lambda e: self._handle_drag_end(e),
            )
            # DragTarget 透明覆盖在卡片上，接收 on_drag_accept 等事件
            target = ft.DragTarget(
                content=draggable,
                on_accept=lambda e, idx=i: self._handle_drop(e, idx),
                on_move=lambda e, idx=i: self._handle_card_drag_move(e, idx),
            )
            target.data = i  # 存储当前卡片的索引
            self.grid.controls.append(target)
        
        # 添加设备按钮卡片放在最后
        if self.add_card:
            self.grid.controls.append(self.add_card)
    
    def _handle_drag_start(self, e, index: int):
        """开始拖拽 - 记录源卡片索引"""
        self._drag_source_index = index
        logger.debug(f"拖拽开始: index={index}")
    
    def _handle_card_drag_move(self, e: ft.DragTargetEvent, target_index: int):
        """拖拽经过卡片 - 高亮目标"""
        if self._drag_source_index is not None and self._drag_source_index != target_index:
            self._drag_target_index = target_index
            self._highlight_target(target_index)
    
    def _handle_drag_end(self, e):
        """结束拖拽"""
        logger.debug(f"拖拽结束")
        self._drag_source_index = None
        self._drag_target_index = None
        self._rebuild_grid()
    
    def _handle_drop(self, e: ft.DragTargetEvent, target_index: int):
        """放置卡片"""
        
        source_idx = self._drag_source_index
        if source_idx is None or source_idx == target_index:
            return
        
        logger.debug(f"放置: source={source_idx}, target={target_index}")
        
        # 重新排序设备列表
        devices = self.devices.copy()
        source_device = devices.pop(source_idx)
        
        # 调整目标索引（如果源在目标之后）
        adjusted_target = target_index
        if source_idx > target_index:
            adjusted_target = target_index
        else:
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
        """高亮目标卡片（通过 DragTarget → Draggable → Stack → Card 找到内部卡片的 Container）"""
        self._rebuild_grid()
        if 0 <= target_index < len(self.grid.controls):
            target_control = self.grid.controls[target_index]
            if isinstance(target_control, ft.DragTarget):
                # DragTarget → Draggable → Stack → DeviceCard
                draggable = target_control.content  # Draggable
                stack = draggable.content  # Stack
                card = stack.content[0]  # DeviceCard (first element in Stack content list)
                if hasattr(card, 'border'):
                    card.border = ft.Border.all(width=2, color=Colors.PRIMARY)
                    card.shadow = ft.BoxShadow(
                        spread_radius=3,
                        blur_radius=12,
                        color="#6366F150",
                    )
                    card.update()


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
