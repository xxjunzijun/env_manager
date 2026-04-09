"""
app/ui/card_grid.py - 卡片网格布局

设备卡片网格容器,支持添加/删除/刷新卡片
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

    自动排列设备卡片,添加按钮卡片放在网格最后
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
            width=999999,  # 极大宽度,确保 Row wrap 能填满可用空间
            bgcolor=Colors.BG,
            padding=16,  # 卡片与背景边界的空隙
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
            # Stack: 卡片在底层,宽高固定以保证 DragTarget 区域有效
            stack = ft.Stack([card], width=220, height=200)
            # 用 Draggable 包装 Stack
            draggable = ft.Draggable(
                content=stack,
                data=i,
                on_drag_start=self._handle_drag_start,
                on_drag_complete=self._handle_drag_end,
            )
            # DragTarget: data=i 存储目标索引，on_accept 通过 e.control.data 读取
            target = ft.DragTarget(
                content=draggable,
                data=i,
                on_accept=lambda e: self._handle_drop(e),
            )
            self.grid.controls.append(target)

        # 添加设备按钮卡片放在最后
        if self.add_card:
            self.grid.controls.append(self.add_card)

    def _handle_drag_start(self, e):
        """开始拖拽 - 记录源卡片索引（从 Draggable.data 读取）"""
        self._drag_source_index = e.data
        logger.debug(f"拖拽开始: source={self._drag_source_index}")

    def _handle_drag_end(self, e):
        """结束拖拽"""
        logger.debug(f"拖拽结束")
        self._drag_source_index = None

    def _handle_drop(self, e):
        """放置卡片（target 从 e.control.data 读取，source 从实例变量读取）"""
        target_idx = e.control.data
        source_idx = self._drag_source_index
        if source_idx is None or target_idx is None or source_idx == target_idx:
            self._rebuild_grid()
            return

        logger.debug(f"放置: source={source_idx}, target={target_idx}")

        # 重新排序设备列表
        devices = self.devices.copy()
        source_device = devices.pop(source_idx)

        # 调整目标索引（pop 后插入位置需重新计算）
        if source_idx < target_idx:
            # 源在前、目标在后：pop 后 target 及之后的索引都-1
            adjusted_target = target_idx - 1
        else:
            # 源在后、目标在前：pop 后 target 及之前不受影响
            adjusted_target = target_idx

        devices.insert(adjusted_target, source_device)
        self.devices = devices

        # 触发重绘
        self._rebuild_grid()

        # 持久化新顺序到数据库
        if self.on_reorder:
            self.on_reorder(self.devices)

        self._drag_source_index = None


class DeviceListView(ft.ListView):
    """
    设备列表视图(替代网格视图)

    适合大量设备的显示,添加按钮卡片放在最后
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

        # 添加设备按钮卡片(放在 ListView 最后)
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
