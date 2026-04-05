"""
app/ui/styles.py - UI 样式定义
"""

import flet as ft


# 颜色主题
class Colors:
    """颜色定义 - 现代深色主题"""
    # 主色调
    PRIMARY = "#6366F1"      # 靛蓝色
    PRIMARY_DARK = "#4F46E5"
    PRIMARY_LIGHT = "#C7D2FE"
    
    # 背景色 - 深色主题
    BG = "#0F172A"           # 深蓝黑
    CARD_BG = "#1E293B"      # 深灰蓝
    CARD_BG_HOVER = "#334155"  # 悬停色
    
    # 状态色
    SUCCESS = "#22C55E"      # 在线/成功 - 绿色
    WARNING = "#F59E0B"      # 警告 - 琥珀色
    ERROR = "#EF4444"        # 离线/错误 - 红色
    INFO = "#64748B"         # 未知/信息 - 灰蓝色
    
    # 文字色
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_DISABLED = "#475569"
    
    # 边框 - 渐变边框色
    BORDER = "#334155"
    BORDER_HOVER = "#6366F1"
    
    # 渐变色
    GRADIENT_START = "#6366F1"
    GRADIENT_END = "#8B5CF6"

    @staticmethod
    def with_opacity(hex_color: str, opacity: float) -> str:
        """将 hex 颜色转为带透明度的 rgba 字符串"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r},{g},{b},{opacity})"
        return hex_color


# 卡片样式 - 现代圆角和阴影
CARD_STYLE = {
    "width": 220,
    "height": 200,
    "border_radius": 16,
    "border": ft.Border.all(width=1, color=Colors.BORDER),
    "bgcolor": Colors.CARD_BG,
    "shadow": ft.BoxShadow(
        spread_radius=1,
        blur_radius=8,
        color="#00000030",
    ),
    "padding": 14,
}

# 悬停样式
CARD_HOVER_STYLE = {
    "border": ft.Border.all(width=2, color=Colors.PRIMARY),
    "shadow": ft.BoxShadow(
        spread_radius=3,
        blur_radius=12,
        color="#6366F140",
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
        "switch": "#A855F7",  # 紫色
        "demo": "#F59E0B",    # 琥珀色
    }
    return colors.get(device_type, Colors.INFO)


def get_status_color(is_online: bool) -> str:
    """获取状态颜色"""
    return Colors.SUCCESS if is_online else Colors.ERROR
