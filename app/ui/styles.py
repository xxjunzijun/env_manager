"""
app/ui/styles.py - UI 样式定义
"""

import flet as ft


# 颜色主题
class Colors:
    """颜色定义"""
    # 主色调
    PRIMARY = "#2196F3"      # 蓝色
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#BBDEFB"
    
    # 背景色
    BG = "#F5F5F5"
    CARD_BG = "#FFFFFF"
    
    # 状态色
    SUCCESS = "#4CAF50"      # 在线/成功
    WARNING = "#FF9800"      # 警告
    ERROR = "#F44336"        # 离线/错误
    INFO = "#9E9E9E"         # 未知/信息
    
    # 文字色
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    
    # 边框
    BORDER = "#E0E0E0"
    BORDER_HOVER = "#9E9E9E"


# 卡片样式
CARD_STYLE = {
    "width": 220,
    "height": 200,
    "border_radius": 12,
    "border": ft.Border.all(width=1, color=Colors.BORDER),
    "bgcolor": Colors.CARD_BG,
    "shadow": ft.BoxShadow(
        spread_radius=1,
        blur_radius=4,
        color="#00000010",
    ),
    "padding": 12,
}

CARD_HOVER_STYLE = {
    "border": ft.Border.all(width=1, color=Colors.PRIMARY),
    "shadow": ft.BoxShadow(
        spread_radius=2,
        blur_radius=8,
        color="#2196F320",
    ),
}

# 按钮样式
BUTTON_STYLE = ft.ButtonStyle(
    bgcolor=Colors.PRIMARY,
    color="white",
    shape=ft.RoundedRectangleBorder(radius=8),
    padding=ft.Padding(16, 8, 16, 8),
)


def get_device_type_color(device_type: str) -> str:
    """获取设备类型对应的颜色"""
    colors = {
        "server": Colors.PRIMARY,
        "switch": "#9C27B0",  # 紫色
    }
    return colors.get(device_type, Colors.INFO)


def get_status_color(is_online: bool) -> str:
    """获取状态颜色"""
    return Colors.SUCCESS if is_online else Colors.ERROR
