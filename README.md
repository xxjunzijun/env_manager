# env_manager

环境变量管理工具 - 轻松管理、切换、备份你的项目环境配置。

## 📖 简介

`env_manager` 是一个用于管理和切换项目环境变量的命令行工具，支持：
- 多环境配置管理（开发、测试、生产）
- 环境变量快速切换
- 配置备份与恢复
- 跨平台支持 (Windows/macOS/Linux)

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/xxjunzijun/env_manager.git
cd env_manager
pip install -e .
```

### 基本用法

```bash
# 查看当前环境
envmanager status

# 切换环境
envmanager switch dev

# 导出当前环境
envmanager export > .env

# 导入环境配置
envmanager import .env
```

## 📁 项目结构

```
env_manager/
├── README.md
├── LICENSE
├── .gitignore
├── setup.py
├── env_manager/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── utils.py
└── tests/
    └── test_env_manager.py
```

## ⚙️ 配置

默认配置文件位于 `~/.envmanager/config.json`

```json
{
  "default_env": "dev",
  "config_dir": "~/.envmanager",
  "backup_enabled": true
}
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

- GitHub: [@xxjunzijun](https://github.com/xxjunzijun)
