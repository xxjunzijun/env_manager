"""
app/data/models.py - 数据模型定义

服务器和交换机共用同一模型，通过 device_type 区分
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Device(SQLModel, table=True):
    """
    设备模型 - 服务器和交换机共用
    
    设备类型:
    - server: 服务器
    - switch: 交换机
    """
    __tablename__ = "devices"
    
    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 基础信息
    name: str = Field(index=True, description="设备名称")
    device_type: str = Field(default="server", description="设备类型: server/switch")
    ip_address: str = Field(description="IP 地址")
    port: int = Field(default=22, description="SSH 端口")
    username: str = Field(description="SSH 用户名")
    password: Optional[str] = Field(default=None, description="SSH 密码（加密存储）")
    
    # 分组和标签
    group: Optional[str] = Field(default=None, description="分组名称")
    tags: Optional[str] = Field(default="", description="标签，逗号分隔")
    
    # SSH 密钥路径（可选）
    ssh_key_path: Optional[str] = Field(default=None, description="SSH 私钥路径")
    
    # 备注
    description: Optional[str] = Field(default=None, description="备注信息")
    
    # 状态
    is_online: bool = Field(default=False, description="是否在线")
    last_check: Optional[datetime] = Field(default=None, description="最后检查时间")
    
    # 扩展信息 (JSON 格式存储)
    ext_info: Optional[str] = Field(default="{}", description="扩展信息 JSON")

    # 是否为示例设备（示例卡片，不可删除）
    is_demo: bool = Field(default=False, description="是否为示例设备")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def tags_list(self) -> list:
        """获取标签列表"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]
    
    @property
    def display_type(self) -> str:
        """显示类型"""
        return "服务器" if self.device_type == "server" else "交换机"
    
    @property
    def ext_data(self) -> dict:
        """获取扩展信息"""
        import json
        try:
            return json.loads(self.ext_info or "{}")
        except:
            return {}


class DeviceHistory(SQLModel, table=True):
    """设备状态历史记录"""
    __tablename__ = "device_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="devices.id")
    check_time: datetime = Field(default_factory=datetime.now)
    is_online: bool = Field(default=False)
    cpu_usage: Optional[float] = Field(default=None)
    memory_usage: Optional[float] = Field(default=None)
    disk_usage: Optional[float] = Field(default=None)
    status_message: Optional[str] = Field(default=None)
