"""
app/data/database.py - 数据库管理
"""

import os
from pathlib import Path
from sqlmodel import SQLEngine
from sqlmodel import create_engine, Session
from app.data.models import Device, DeviceHistory


# 项目根目录 (相对于当前文件)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据库路径 (项目相对路径)
DATA_DIR = PROJECT_ROOT / ".env_manager"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "env_manager.db"


def get_engine():
    """获取数据库引擎"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return engine


def init_database():
    """初始化数据库"""
    from sqlmodel.metadata import Metadata
    
    engine = get_engine()
    metadata = Metadata()
    metadata.create_all(engine)
    
    # 如果需要迁移，可以在这里处理
    return engine


def get_session():
    """获取数据库会话"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


class DeviceDB:
    """设备数据库操作类"""
    
    def __init__(self):
        self.engine = get_engine()
    
    def add_device(self, device: Device) -> int:
        """添加设备"""
        with Session(self.engine) as session:
            session.add(device)
            session.commit()
            session.refresh(device)
            return device.id
    
    def get_device(self, device_id: int) -> Device:
        """获取设备"""
        with Session(self.engine) as session:
            return session.get(Device, device_id)
    
    def get_all_devices(self) -> list[Device]:
        """获取所有设备"""
        with Session(self.engine) as session:
            return session.query(Device).all()
    
    def get_devices_by_type(self, device_type: str) -> list[Device]:
        """按类型获取设备"""
        with Session(self.engine) as session:
            return session.query(Device).filter(Device.device_type == device_type).all()
    
    def get_devices_by_group(self, group: str) -> list[Device]:
        """按分组获取设备"""
        with Session(self.engine) as session:
            return session.query(Device).filter(Device.group == group).all()
    
    def update_device(self, device_id: int, **kwargs) -> bool:
        """更新设备"""
        from datetime import datetime
        kwargs["updated_at"] = datetime.now()
        
        with Session(self.engine) as session:
            device = session.get(Device, device_id)
            if not device:
                return False
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            session.commit()
            return True
    
    def delete_device(self, device_id: int) -> bool:
        """删除设备"""
        with Session(self.engine) as session:
            device = session.get(Device, device_id)
            if not device:
                return False
            session.delete(device)
            session.commit()
            return True
    
    def get_all_groups(self) -> list[str]:
        """获取所有分组"""
        with Session(self.engine) as session:
            groups = session.query(Device.group).distinct().all()
            return [g[0] for g in groups if g[0]]
