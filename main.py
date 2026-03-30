"""
env_manager - 服务器/交换机可视化管理系统
程序入口
"""

import flet as ft
from app.ui.main_window import MainWindow
from app.data.database import init_database
from app.utils.logger import setup_logger


def main(page: ft.Page):
    """主程序入口"""
    # 初始化日志
    logger = setup_logger()
    logger.info("=" * 50)
    logger.info("env_manager 启动")
    logger.info("=" * 50)
    
    # 初始化数据库
    init_database()
    logger.info("数据库初始化完成")
    
    # 创建主窗口
    app = MainWindow(page)
    app.run()


if __name__ == "__main__":
    # 新版本 Flet 使用 ft.run() 替代 ft.app()
    # 旧版: ft.app(target=main)
    # 新版: ft.run(main)
    ft.run(main)
