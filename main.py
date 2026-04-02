"""
env_manager - 服务器/交换机可视化管理系统
程序入口
"""

import flet as ft
import sys
import traceback
from app.ui.main_window import MainWindow
from app.data.database import init_database
from app.utils.logger import setup_logger, get_log_dir, LOG_FILE


# 全局 Page 引用，用于错误弹窗
_main_page = None


def show_error_dialog(page: ft.Page, title: str, message: str, details: str = None):
    """显示错误对话框
    
    Args:
        page: Flet Page 实例
        title: 错误标题
        message: 错误消息
        details: 详细错误信息（可选）
    """
    content = ft.Column([
        ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
        ft.Container(height=10),
        ft.Text(message, size=14),
    ], scroll="auto")
    
    if details:
        content.controls.append(ft.Container(height=10))
        content.controls.append(
            ft.Container(
                content=ft.Text(details, size=11, font_family="monospace"),
                bgcolor=ft.Colors.with_opacity(ft.Colors.GREY_200, 0.3),
                padding=10,
                border_radius=5,
                height=200,
            )
        )
    
    # 添加日志路径提示
    content.controls.append(ft.Container(height=10))
    content.controls.append(
        ft.Text(f"日志文件: {get_log_dir()}", size=11, color=ft.Colors.GREY_600)
    )
    
    def close_and_exit(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("错误"),
        content=content,
        actions=[
            ft.TextButton("确定", on_click=close_and_exit),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.dialog = dialog
    dialog.open = True
    page.update()


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常捕获"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 忽略 Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 格式化错误信息
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    logger = get_logger()
    logger.critical(f"未捕获的异常: {exc_value}\n{error_msg}")
    
    # 如果有 Page 实例，显示错误弹窗
    if _main_page:
        error_lines = str(exc_value).split('\n')
        title = f"程序错误: {exc_type.__name__}"
        message = error_lines[0] if error_lines else str(exc_value)
        
        # 简化 traceback 显示
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_short = '\n'.join(tb_lines[-5:])  # 只显示最后5行
        
        def show_dialog():
            show_error_dialog(_main_page, title, message, tb_short)
        
        _main_page.loop.call_later(0, show_dialog)


def main(page: ft.Page):
    """主程序入口"""
    global _main_page
    _main_page = page
    
    # 设置全局异常捕获
    sys.excepthook = global_exception_handler
    
    # 初始化日志
    logger = setup_logger()
    logger.info("=" * 50)
    logger.info("env_manager 启动")
    logger.info("=" * 50)
    
    try:
        # 初始化数据库
        init_database()
        logger.info("数据库初始化完成")
        
        # 创建主窗口
        app = MainWindow(page)
        app.run()
        
    except Exception as e:
        logger.critical(f"启动失败: {e}")
        # 初始化失败时也尝试显示错误
        try:
            error_msg = f"程序启动失败:\n\n{type(e).__name__}: {e}\n\n请查看日志文件: {LOG_FILE}"
            page.add(ft.Text(error_msg))
            page.update()
        except:
            pass


if __name__ == "__main__":
    # 新版本 Flet 使用 ft.run() 替代 ft.app()
    # 旧版: ft.app(target=main)
    # 新版: ft.run(main)
    ft.run(main)
