"""
app/ui/server_dialog.py - 设备编辑对话框

添加/编辑服务器或交换机
"""

import flet as ft
from typing import Callable, Optional
from app.data.models import Device
from app.ui.styles import Colors, BUTTON_STYLE
from app.core.ssh_manager import ssh_manager


class DeviceDialog(ft.AlertDialog):
    """
    设备编辑对话框
    
    用于添加新设备或编辑现有设备
    """
    
    def __init__(
        self,
        device: Optional[Device] = None,
        on_save: Callable[[Device], None] = None,
        on_delete: Callable[[int], None] = None,
    ):
        self.device = device
        self.on_save = on_save
        self.on_delete = on_delete
        self.is_edit = device is not None
        
        # 状态变量
        self.test_result = ft.Ref[ft.Text]()
        self.test_progress = ft.Ref[ft.ProgressBar]()
        self.save_btn = ft.Ref[ft.ElevatedButton]()
        
        # 设备类型选择
        self.type_segmented = ft.SegmentedButton(
            segments=[
                ft.Segment(
                    value="server",
                    label=ft.Text("🖥️ 服务器"),
                ),
                ft.Segment(
                    value="switch",
                    label=ft.Text("🔌 交换机"),
                ),
            ],
            selected={"server" if not self.is_edit or device.device_type == "server" else "switch"},
            on_change=self._on_type_change,
        )
        
        # 表单字段
        self.name_field = ft.TextField(
            label="名称",
            hint_text="如: 生产环境-Web-01",
            value=device.name if self.is_edit else "",
            autofocus=True,
        )
        
        self.ip_field = ft.TextField(
            label="IP 地址",
            hint_text="如: 192.168.1.100",
            value=device.ip_address if self.is_edit else "",
            keyboard_type=ft.KeyboardType.URL,
        )
        
        self.port_field = ft.TextField(
            label="端口",
            hint_text="SSH 端口，默认 22",
            value=str(device.port) if self.is_edit else "22",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120,
        )
        
        self.username_field = ft.TextField(
            label="用户名",
            hint_text="SSH 用户名",
            value=device.username if self.is_edit else "",
        )
        
        self.password_field = ft.TextField(
            label="密码",
            hint_text="SSH 密码",
            value=device.password or "",
            password=True,
            can_reveal_password=True,
        )
        
        self.ssh_key_field = ft.TextField(
            label="SSH 密钥路径 (可选)",
            hint_text="如: ~/.ssh/id_rsa",
            value=device.ssh_key_path or "",
        )
        
        self.group_field = ft.TextField(
            label="分组 (可选)",
            hint_text="如: 生产环境、测试环境",
            value=device.group or "",
        )
        
        self.tags_field = ft.TextField(
            label="标签 (可选)",
            hint_text="逗号分隔，如: web, db, nginx",
            value=device.tags or "",
        )
        
        self.description_field = ft.TextField(
            label="备注 (可选)",
            hint_text="其他说明...",
            value=device.description or "",
            max_lines=2,
        )
        
        # 状态显示
        self.status_text = ft.Text(ref=self.test_result, size=12, color=Colors.TEXT_SECONDARY)
        self.test_progress_bar = ft.ProgressBar(ref=self.test_progress, visible=False)
        
        super().__init__(
            modal=True,
            title=ft.Row(
                [
                    ft.Text("📝 编辑设备" if self.is_edit else "➕ 添加设备"),
                ]
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        # 设备类型
                        ft.Text("设备类型", size=12, color=Colors.TEXT_SECONDARY),
                        self.type_segmented,
                        ft.Container(height=8),
                        
                        # 基本信息
                        self.name_field,
                        ft.Row([self.ip_field, self.port_field]),
                        self.username_field,
                        self.password_field,
                        self.ssh_key_field,
                        
                        ft.Divider(),
                        
                        # 附加信息
                        self.group_field,
                        self.tags_field,
                        self.description_field,
                        
                        # 测试连接状态
                        self.test_progress_bar,
                        self.status_text,
                    ],
                    tight=True,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                padding=10,
            ),
            actions=[
                # 删除按钮（编辑时显示）
                ft.TextButton(
                    "删除",
                    on_click=self._handle_delete,
                    style=ft.TextButtonStyle(color=Colors.ERROR),
                    visible=self.is_edit,
                ),
                ft.TextButton(
                    "取消",
                    on_click=self._handle_cancel,
                ),
                ft.TextButton(
                    "测试连接",
                    on_click=self._handle_test,
                ),
                ft.ElevatedButton(
                    "保存",
                    ref=self.save_btn,
                    on_click=self._handle_save,
                    style=BUTTON_STYLE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _on_type_change(self, e):
        """设备类型变更"""
        self.update()
    
    def _handle_test(self, e):
        """测试连接"""
        import threading
        
        # 验证必填字段
        if not self._validate_fields(show_message=False):
            self.test_result.current.value = "请填写必填字段"
            self.test_result.current.color = Colors.ERROR
            self.update()
            return
        
        self.test_progress_bar.current.visible = True
        self.test_result.current.value = "正在测试连接..."
        self.test_result.current.color = Colors.INFO
        self.save_btn.current.disabled = True
        self.update()
        
        def test():
            try:
                success, message = ssh_manager.test_connection(
                    host=self.ip_field.value,
                    port=int(self.port_field.value or 22),
                    username=self.username_field.value,
                    password=self.password_field.value or None,
                    ssh_key_path=self.ssh_key_field.value or None,
                )
                
                # 在主线程更新 UI - 使用 call_later
                def update_ui():
                    self.test_progress_bar.current.visible = False
                    if success:
                        self.test_result.current.value = f"[OK] {message}"
                        self.test_result.current.color = Colors.SUCCESS
                    else:
                        self.test_result.current.value = f"[X] {message}"
                        self.test_result.current.color = Colors.ERROR
                    self.save_btn.current.disabled = False
                    self.update()
                
                self.page.call_later(0, update_ui)
                
            except Exception as ex:
                def update_ui():
                    self.test_progress_bar.current.visible = False
                    self.test_result.current.value = f"[X] 测试失败: {str(ex)}"
                    self.test_result.current.color = Colors.ERROR
                    self.save_btn.current.disabled = False
                    self.update()
                
                self.page.call_later(0, update_ui)
        
        threading.Thread(target=test, daemon=True).start()
    
    def _handle_save(self, e):
        """保存设备"""
        if not self._validate_fields():
            return
        
        # 创建或更新设备对象
        if self.is_edit:
            device = self.device
            device.name = self.name_field.value
            device.device_type = list(self.type_segmented.selected)[0]
            device.ip_address = self.ip_field.value
            device.port = int(self.port_field.value or 22)
            device.username = self.username_field.value
            device.password = self.password_field.value or None
            device.ssh_key_path = self.ssh_key_field.value or None
            device.group = self.group_field.value or None
            device.tags = self.tags_field.value or ""
            device.description = self.description_field.value or None
        else:
            device = Device(
                name=self.name_field.value,
                device_type=list(self.type_segmented.selected)[0],
                ip_address=self.ip_field.value,
                port=int(self.port_field.value or 22),
                username=self.username_field.value,
                password=self.password_field.value or None,
                ssh_key_path=self.ssh_key_field.value or None,
                group=self.group_field.value or None,
                tags=self.tags_field.value or "",
                description=self.description_field.value or None,
            )
        
        if self.on_save:
            self.on_save(device)
        
        self.open = False
        self.update()
    
    def _handle_delete(self, e):
        """删除设备"""
        if self.is_edit and self.on_delete:
            self.on_delete(self.device.id)
        self.open = False
        self.update()
    
    def _handle_cancel(self, e):
        """取消"""
        self.open = False
        self.update()
    
    def _validate_fields(self, show_message=True) -> bool:
        """验证必填字段"""
        errors = []
        
        if not self.name_field.value.strip():
            errors.append("名称")
        if not self.ip_field.value.strip():
            errors.append("IP 地址")
        if not self.username_field.value.strip():
            errors.append("用户名")
        
        # 验证 IP 格式
        if self.ip_field.value.strip():
            import re
            ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
            if not re.match(ip_pattern, self.ip_field.value.strip()):
                errors.append("IP 格式")
        
        if errors and show_message:
            self.test_result.current.value = f"请填写: {', '.join(errors)}"
            self.test_result.current.color = Colors.ERROR
            self.update()
        
        return len(errors) == 0
