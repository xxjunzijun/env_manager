"""
app/data/database.py - 数据库管理

设备数据的持久化存储
- SQLite 数据库
- 设备 CRUD 操作
"""

import os
from pathlib import Path
from sqlmodel import create_engine, Session, select
from app.data.models import Device, DeviceHistory
from app.utils.logger import get_logger


# 项目根目录 (相对于当前文件)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据库路径 (项目相对路径)
DATA_DIR = PROJECT_ROOT / ".env_manager"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "env_manager.db"

# 获取子 Logger
logger = get_logger("database")


def get_engine():
    """获取数据库引擎"""
    logger.debug(f"初始化数据库引擎: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return engine


def init_database():
    """初始化数据库"""
    logger.info("初始化数据库...")
    engine = get_engine()
    Device.metadata.create_all(engine)
    DeviceHistory.metadata.create_all(engine)
    _migrate_if_needed(engine)
    logger.info(f"数据库初始化完成: {DB_PATH}")
    return engine


def _migrate_if_needed(engine):
    """迁移旧数据库：添加新列（如果不存在）"""
    from sqlalchemy import text
    with engine.connect() as conn:
        # 检查 devices 表是否有 is_demo 列
        try:
            conn.execute(text("SELECT is_demo FROM devices LIMIT 1"))
            logger.debug("is_demo 列已存在，无需迁移")
        except Exception:
            logger.warning("检测到旧数据库，添加 is_demo 列...")
            try:
                conn.execute(text("ALTER TABLE devices ADD COLUMN is_demo BOOLEAN DEFAULT 0"))
                conn.commit()
                logger.info("is_demo 列添加成功")
            except Exception as e:
                logger.error(f"is_demo 列迁移失败: {e}")
        
        # 检查 devices 表是否有 display_order 列
        try:
            conn.execute(text("SELECT display_order FROM devices LIMIT 1"))
            logger.debug("display_order 列已存在，无需迁移")
        except Exception:
            logger.warning("检测到旧数据库，添加 display_order 列...")
            try:
                conn.execute(text("ALTER TABLE devices ADD COLUMN display_order INTEGER DEFAULT 0"))
                conn.commit()
                logger.info("display_order 列添加成功")
            except Exception as e:
                logger.error(f"display_order 列迁移失败: {e}")


def get_session():
    """获取数据库会话"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


class DeviceDB:
    """设备数据库操作类"""
    
    def __init__(self):
        self.engine = get_engine()
        logger.debug("DeviceDB 实例创建")
    
    def add_device(self, device: Device) -> int:
        """添加设备"""
        logger.info(f"添加设备: name={device.name}, type={device.device_type}, ip={device.ip_address}")
        with Session(self.engine) as session:
            # 获取当前最大 display_order
            max_order = session.exec(
                select(Device.display_order).order_by(Device.display_order.desc()).limit(1)
            ).first()
            device.display_order = (max_order or 0) + 1
            
            session.add(device)
            session.commit()
            session.refresh(device)
            logger.info(f"设备添加成功: id={device.id}, name={device.name}")
            return device.id
    
    def get_device(self, device_id: int) -> Device:
        """获取设备"""
        logger.debug(f"查询设备: id={device_id}")
        with Session(self.engine) as session:
            device = session.get(Device, device_id)
            if device:
                logger.debug(f"设备找到: id={device_id}, name={device.name}")
            else:
                logger.warning(f"设备不存在: id={device_id}")
            return device
    
    def get_all_devices(self) -> list[Device]:
        """获取所有设备（按显示顺序排序）"""
        logger.debug("查询所有设备")
        with Session(self.engine) as session:
            devices = session.exec(
                select(Device).order_by(Device.display_order, Device.id)
            ).all()
            logger.debug(f"设备列表查询完成: 共 {len(devices)} 台")
            return devices
    
    def get_devices_by_type(self, device_type: str) -> list[Device]:
        """按类型获取设备"""
        logger.debug(f"按类型查询设备: type={device_type}")
        with Session(self.engine) as session:
            devices = session.exec(select(Device).where(Device.device_type == device_type)).all()
            logger.debug(f"类型查询完成: {device_type} 共 {len(devices)} 台")
            return devices
    
    def get_devices_by_group(self, group: str) -> list[Device]:
        """按分组获取设备"""
        logger.debug(f"按分组查询设备: group={group}")
        with Session(self.engine) as session:
            devices = session.exec(select(Device).where(Device.group == group)).all()
            logger.debug(f"分组查询完成: {group} 共 {len(devices)} 台")
            return devices
    
    def update_device(self, device_id: int, **kwargs) -> bool:
        """更新设备"""
        from datetime import datetime
        kwargs["updated_at"] = datetime.now()
        
        logger.info(f"更新设备: id={device_id}, 更新字段: {list(kwargs.keys())}")
        with Session(self.engine) as session:
            device = session.get(Device, device_id)
            if not device:
                logger.warning(f"更新失败 - 设备不存在: id={device_id}")
                return False
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            session.commit()
            logger.info(f"设备更新成功: id={device_id}")
            return True
    
    def delete_device(self, device_id: int) -> bool:
        """删除设备"""
        logger.info(f"删除设备: id={device_id}")
        with Session(self.engine) as session:
            device = session.get(Device, device_id)
            if not device:
                logger.warning(f"删除失败 - 设备不存在: id={device_id}")
                return False
            device_name = device.name
            session.delete(device)
            session.commit()
            logger.info(f"设备删除成功: id={device_id}, name={device_name}")
            return True
    
    def get_all_groups(self) -> list[str]:
        """获取所有分组"""
        logger.debug("查询所有分组")
        with Session(self.engine) as session:
            groups = session.exec(select(Device.group).distinct()).all()
            result = [g for g in groups if g is not None]
            logger.debug(f"分组列表: {result}")
            return result
