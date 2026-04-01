"""
app/ui/server_dialog.py - 设备编辑对话框

添加/编辑服务器或交换机。使用自定义 ModalOverlay 而非 AlertDialog，
确保在任意点击源（IconButton / Container.on_click）下都能可靠显示。
"""

import flet as ft
from typing import Callable, Optional
from app.data.models import Device
from app.ui.styles import Colors, BUTTON_STYLE
from app.core.ssh_manager import ssh_manager
from app.utils.logger import get_logger


logger = get_logger("ui.dialog")


class DeviceDialogModal(ft.Container):
    """
    设备编辑对话框 - 自定义 Modal Overlay 版本

    不依赖 page.dialog + page.update() 时序，
    直接通过 visible 属性控制显示/隐藏。
    """

    def __init__(
        self,
        page: ft.Page,
        device: Optional[Device] = None,
        on_save: Callable[[Device], None] = None,
        on_delete: Callable[[int], None] = None,
    ):
        self._page = page
        self.device = device
        self.on_save = on_save
        self.on_delete = on_delete
        self.is_edit = device is not None
        self._visible = False

        logger.debug(f"DeviceDialogModal 创建: is_edit={self.is_edit}, device={device.name if device else 'None'}")

        # 状态 Refs
        self.test_result_ref = ft.Ref[ft.Text]()
        self.test_progress_ref = ft.Ref[ft.ProgressBar]()
        self.save_btn_ref = ft.Ref[ft.ElevatedButton]()

        # ---- 表单内容 ----
        title_text = "[EDIT] 编辑设备" if self.is_edit else "[+] 添加设备"

        self.type_segmented = ft.SegmentedButton(
            segments=[
                ft.Segment(value="server", label=ft.Text("[SVR] 服务器")),
                ft.Segment(value="switch", label=ft.Text("[SW] 交换机")),
            ],
            selected={"server" if not self.is_edit or device.device_type == "server" else "switch"},
            on_change=self._on_type_change,
        )

        self.name_field = ft.TextField(
            label="名称", hint_text="如: 生产环境-Web-01",
            value=device.name if self.is_edit else "", autofocus=True,
        )
        self.ip_field = ft.TextField(
            label="IP 地址", hint_text="如: 192.168.1.100",
            value=device.ip_address if self.is_edit else "",
            keyboard_type=ft.KeyboardType.URL,
        )
        self.port_field = ft.TextField(
            label="端口", hint_text="SSH 端口，默认 22",
            value=str(device.port) if self.is_edit else "22",
            keyboard_type=ft.KeyboardType.NUMBER, width=120,
        )
        self.username_field = ft.TextField(
            label="用户名", hint_text="SSH 用户名",
            value=device.username if self.is_edit else "",
        )
        self.password_field = ft.TextField(
            label="密码", hint_text="SSH 密码",
            value=device.password if self.is_edit else "",
            password=True, can_reveal_password=True,
        )
        self.ssh_key_field = ft.TextField(
            label="SSH 密钥路径 (可选)", hint_text="如: ~/.ssh/id_rsa",
            value=device.ssh_key_path if self.is_edit else "",
        )
        self.group_field = ft.TextField(
            label="分组 (可选)", hint_text="如: 生产环境、测试环境",
            value=device.group if self.is_edit else "",
        )
        self.tags_field = ft.TextField(
            label="标签 (可选)", hint_text="逗号分隔，如: web, db, nginx",
            value=device.tags if self.is_edit else "",
        )
        self.description_field = ft.TextField(
            label="备注 (可选)", hint_text="其他说明...",
            value=device.description if self.is_edit else "", max_lines=2,
        )
        self.status_text = ft.Text(ref=self.test_result_ref, size=12, color=Colors.TEXT_SECONDARY)
        self.test_progress_bar = ft.ProgressBar(ref=self.test_progress_ref, visible=False)

        form = ft.Column(
            [
                ft.Text("设备类型", size=12, color=Colors.TEXT_SECONDARY),
                self.type_segmented,
                ft.Container(height=8),
                self.name_field,
                ft.Row([self.ip_field, self.port_field]),
                self.username_field,
                self.password_field,
                self.ssh_key_field,
                ft.Divider(),
                self.group_field,
                self.tags_field,
                self.description_field,
                self.test_progress_bar,
                self.status_text,
            ],
            tight=True, spacing=8, scroll=ft.ScrollMode.AUTO,
        )

        actions_row = ft.Row(
            [
                ft.TextButton("删除", on_click=self._handle_delete,
                              style=ft.ButtonStyle(color=Colors.ERROR),
                              visible=self.is_edit),
                ft.Container(expand=True),
                ft.TextButton("取消", on_click=self._handle_cancel),
                ft.TextButton("测试连接", on_click=self._handle_test),
                ft.ElevatedButton("保存", ref=self.save_btn_ref,
                                  on_click=self._handle_save, style=BUTTON_STYLE),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

        dialog_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=4),
                    form,
                    ft.Container(height=8),
                    actions_row,
                ],
                tight=True, spacing=0,
            ),
            width=420, padding=16,
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
                    # 半透明遮罩（点击关闭）
                    ft.Container(
                        expand=True,
                        bgcolor="#00000080",
                        on_click=self._handle_cancel,
                    ),
                    # 居中对话框
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

    # ---- 生命周期控制 ----

    def show(self):
        """显示对话框"""
        self.visible = True
        if self not in self._page.controls:
            self._page.add(self)
        self._page.update()
        logger.debug("DeviceDialogModal 已显示")

    def hide(self):
        """关闭对话框"""
        self.visible = False
        self._page.update()
        logger.debug("DeviceDialogModal 已隐藏")

    # ---- 事件处理 ----

    def _on_type_change(self, e):
        self.update()

    def _handle_test(self, e):
        """测试连接"""
        import threading
        if not self._validate_fields(show_message=False):
            self.test_result_ref.current.value = "请填写必填字段"
            self.test_result_ref.current.color = Colors.ERROR
            self.update()
            return

        logger.info(f"测试连接: {self.username_field.value}@{self.ip_field.value}:{self.port_field.value}")
        self.test_progress_ref.current.visible = True
        self.test_result_ref.current.value = "正在测试连接..."
        self.test_result_ref.current.color = Colors.INFO
        self.save_btn_ref.current.disabled = True
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
                def update_ui():
                    self.test_progress_ref.current.visible = False
                    if success:
                        self.test_result_ref.current.value = f"[OK] {message}"
                        self.test_result_ref.current.color = Colors.SUCCESS
                    else:
                        self.test_result_ref.current.value = f"[X] {message}"
                        self.test_result_ref.current.color = Colors.ERROR
                    self.save_btn_ref.current.disabled = False
                    self.update()
                self._page.call_later(0, update_ui)
            except Exception as ex:
                def update_ui():
                    self.test_progress_ref.current.visible = False
                    self.test_result_ref.current.value = f"[X] 测试失败: {str(ex)}"
                    self.test_result_ref.current.color = Colors.ERROR
                    self.save_btn_ref.current.disabled = False
                    self.update()
                self._page.call_later(0, update_ui)

        threading.Thread(target=test, daemon=True).start()

    def _handle_save(self, e):
        """保存设备"""
        if not self._validate_fields():
            return
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
        self.hide()

    def _handle_delete(self, e):
        """删除设备"""
        if self.is_edit and self.on_delete:
            self.on_delete(self.device.id)
        self.hide()

    def _handle_cancel(self, e=None):
        """取消"""
        self.hide()

    def _validate_fields(self, show_message=True) -> bool:
        """验证必填字段"""
        errors = []
        if not self.name_field.value.strip():
            errors.append("名称")
        if not self.ip_field.value.strip():
            errors.append("IP 地址")
        if not self.username_field.value.strip():
            errors.append("用户名")
        if self.ip_field.value.strip():
            import re
            if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", self.ip_field.value.strip()):
                errors.append("IP 格式")
        if errors and show_message:
            self.test_result_ref.current.value = f"请填写: {', '.join(errors)}"
            self.test_result_ref.current.color = Colors.ERROR
            self.update()
        return len(errors) == 0


# ---- 保留旧类名作为别名（兼容已有代码） ----
DeviceDialog = DeviceDialogModal
