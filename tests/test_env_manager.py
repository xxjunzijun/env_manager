"""
env_manager - 测试文件
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from env_manager.config import Config
from env_manager.utils import switch_env, export_env


class TestConfig(unittest.TestCase):
    """配置测试"""
    
    def test_config_init(self):
        """测试配置初始化"""
        config = Config()
        self.assertIsNotNone(config.config_dir)
        self.assertIsNotNone(config.envs_dir)
    
    def test_get_set(self):
        """测试配置读写"""
        config = Config()
        test_key = "_test_key"
        test_value = "_test_value"
        
        config.set(test_key, test_value)
        self.assertEqual(config.get(test_key), test_value)
        
        # 清理测试数据
        config.set(test_key, None)


class TestUtils(unittest.TestCase):
    """工具函数测试"""
    
    def test_switch_env(self):
        """测试环境切换"""
        # 测试切换（前提是环境已存在）
        pass


if __name__ == "__main__":
    unittest.main()
