"""
env_manager - 主程序入口
"""

import argparse
import sys

from .config import Config
from .utils import print_status, switch_env, export_env, import_env


def main():
    parser = argparse.ArgumentParser(
        description="env_manager - 环境变量管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status 命令
    subparsers.add_parser("status", help="查看当前环境状态")

    # switch 命令
    switch_parser = subparsers.add_parser("switch", help="切换环境")
    switch_parser.add_argument("env", help="目标环境名称")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出当前环境配置")
    export_parser.add_argument("-o", "--output", help="输出文件路径")

    # import 命令
    import_parser = subparsers.add_parser("import", help="导入环境配置")
    import_parser.add_argument("file", help="配置文件路径")

    args = parser.parse_args()

    if args.command == "status":
        print_status()
    elif args.command == "switch":
        switch_env(args.env)
    elif args.command == "export":
        export_env(args.output)
    elif args.command == "import":
        import_env(args.file)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
