"""
env_manager - 配置文件
"""

import os
import json
from pathlib import Path


class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        "default_env": "dev",
        "config_dir": "~/.envmanager",
        "backup_enabled": True
    }
    
    def __init__(self):
        self.config_dir = Path(os.path.expanduser("~/.envmanager"))
        self.config_file = self.config_dir / "config.json"
        self.envs_dir = self.config_dir / "envs"
        self._ensure_dirs()
        self._ensure_config()
    
    def _ensure_dirs(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.envs_dir.mkdir(parents=True, exist_ok=True)
    
    def _ensure_config(self):
        """确保配置文件存在"""
        if not self.config_file.exists():
            self._save_config(self.DEFAULT_CONFIG)
    
    def _load_config(self):
        """加载配置"""
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_config(self, config):
        """保存配置"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        """获取配置项"""
        config = self._load_config()
        return config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        config = self._load_config()
        config[key] = value
        self._save_config(config)
    
    @property
    def current_env(self):
        """获取当前环境"""
        return self.get("current_env", self.get("default_env", "dev"))
