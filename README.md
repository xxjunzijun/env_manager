# env_manager

🖥️ 服务器/交换机可视化管理系统

一个基于 Flet 的跨平台桌面应用，用于管理和监控服务器及交换机设备。

## 功能特性

- ✅ **可视化卡片管理** - 每个设备显示为独立的卡片，一目了然
- 🔄 **实时数据刷新** - 点击刷新获取服务器实时状态
- 🔌 **SSH 连接** - 支持密码和密钥认证
- 📊 **可扩展插件系统** - 新增功能只需添加插件
- 🗂️ **分组管理** - 按分组和标签组织设备
- 🔍 **快速搜索** - 支持按名称、IP、标签搜索

## 支持的设备

| 类型 | 图标 | 支持的插件 |
|------|------|-----------|
| 服务器 | 🖥️ | 系统信息、网络信息 |
| 交换机 | 🔌 | 端口状态、VLAN 信息 |

## 技术栈

| 组件 | 技术 |
|------|------|
| UI 框架 | Flet (Flutter for Python) |
| SSH | Paramiko |
| 数据库 | SQLite (SQLModel) |
| Python | 3.8+ |

## 项目结构

```
env_manager/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖
├── README.md
├── app/
│   ├── ui/                 # UI 组件
│   │   ├── main_window.py  # 主窗口
│   │   ├── card_widget.py  # 设备卡片
│   │   ├── card_grid.py    # 卡片网格
│   │   ├── server_dialog.py # 设备编辑弹窗
│   │   └── styles.py       # 样式定义
│   ├── core/               # 核心功能
│   │   ├── ssh_manager.py  # SSH 连接管理
│   │   └── card_plugin.py  # 卡片插件系统
│   ├── data/               # 数据层
│   │   ├── models.py       # 数据模型
│   │   └── database.py    # 数据库操作
│   ├── plugins/            # 插件
│   │   ├── sys_info.py     # 系统信息插件
│   │   ├── network_info.py # 网络信息插件
│   │   └── switch_info.py  # 交换机插件
│   └── utils/              # 工具
│       └── logger.py       # 日志
└── tests/
```

## 数据存储

数据存储在项目目录内的 `.env_manager/` 文件夹中：

```
env_manager/
├── .env_manager/           # 项目数据目录
│   ├── env_manager.db      # SQLite 数据库
│   └── logs/              # 日志文件
└── ...
```

> ⚠️ **注意**：`.env_manager/` 目录已添加到 `.gitignore`，不会被提交到 Git

## 安装

```bash
# 克隆项目
git clone https://github.com/xxjunzijun/env_manager.git
cd env_manager

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用方法

### 添加设备

1. 点击卡片区域的「➕ 添加设备」
2. 选择设备类型（服务器/交换机）
3. 填写 SSH 连接信息
4. 点击「测试连接」验证
5. 点击「保存」

### 编辑设备

点击任意设备卡片即可编辑

### 刷新设备

点击卡片上的「刷新」按钮获取最新数据

## 插件开发

新增功能只需创建插件类：

```python
from app.core.card_plugin import BaseCardPlugin, PluginInfo, register_plugin

@register_plugin
class MyPlugin(BaseCardPlugin):
    info = PluginInfo(
        name="my_plugin",
        version="1.0.0",
        description="我的插件",
        icon="📦",
        supported_types=["server"],
        priority=30,
    )
    
    def fetch(self, ssh_conn):
        # 获取数据
        return {"key": "value"}
    
    def render(self, data):
        # 渲染显示
        return [{"label": "标签", "value": data["key"], "icon": "📦"}]
```

## 许可证

MIT License
