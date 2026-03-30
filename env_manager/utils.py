"""
env_manager - 工具函数
"""

import os
import json
from pathlib import Path
from .config import Config


def print_status():
    """打印当前环境状态"""
    config = Config()
    current = config.current_env
    env_file = config.envs_dir / f"{current}.json"
    
    print(f"📦 env_manager")
    print(f"━━━━━━━━━━━━━━━━━━━━")
    print(f"🌍 当前环境: {current}")
    print(f"📂 配置目录: {config.config_dir}")
    print(f"📄 环境文件: {env_file}")
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_data = json.load(f)
        print(f"📊 变量数量: {len(env_data.get('vars', {}))}")
    else:
        print(f"⚠️  未找到环境配置文件")


def switch_env(env_name: str):
    """切换环境"""
    config = Config()
    env_file = config.envs_dir / f"{env_name}.json"
    
    if not env_file.exists():
        print(f"❌ 环境 '{env_name}' 不存在")
        print(f"💡 使用 'envmanager init {env_name}' 创建新环境")
        return
    
    config.set("current_env", env_name)
    print(f"✅ 已切换到环境: {env_name}")


def export_env(output_file: str = None):
    """导出当前环境配置"""
    config = Config()
    current = config.current_env
    env_file = config.envs_dir / f"{current}.json"
    
    if not env_file.exists():
        print(f"❌ 当前环境 '{current}' 没有配置文件")
        return
    
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已导出到: {output_file}")
    else:
        print(content)


def import_env(file_path: str):
    """导入环境配置"""
    config = Config()
    env_file = Path(file_path)
    
    if not env_file.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    current = config.current_env
    dest_file = config.envs_dir / f"{current}.json"
    
    with open(env_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with open(dest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已导入到环境: {current}")
