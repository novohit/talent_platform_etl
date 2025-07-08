import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from threading import Lock

from sqlmodel import Session, select, desc
from talent_platform.db.database import get_session
from talent_platform.logger import logger


@dataclass
class ChangeEvent:
    """数据库变更事件"""
    table_name: str
    operation: str  # INSERT, UPDATE, DELETE
    record_id: Any
    timestamp: datetime
    old_data: Optional[Dict] = None
    new_data: Optional[Dict] = None
    trigger_plugins: List[str] = None
    
    def __post_init__(self):
        if self.trigger_plugins is None:
            self.trigger_plugins = []


class DatabaseMonitor:
    """数据库变更监听器"""
    
    def __init__(self):
        self.last_check_time = datetime.now()
        self.monitored_tables = {}  # table_name -> trigger_config
        self.change_handlers = {}  # table_name -> handler_function
        self._lock = Lock()
        
        # 加载监听配置
        self._load_monitor_config()
    
    def _load_monitor_config(self):
        """加载监听配置"""
        # 这里可以从配置文件或数据库加载
        # 示例配置
        self.monitored_tables = {
            "derived_intl_teacher_data": {
                "triggers": ["data_processor", "es_indexer"],
                "conditions": {"is_valid": True},
                "operations": ["INSERT", "UPDATE"]
            },
            "data_intl_wide_view": {
                "triggers": ["teacher_analyzer", "report_generator"],
                "conditions": {},
                "operations": ["INSERT", "UPDATE", "DELETE"]
            }
        }
        logger.info(f"Loaded monitor config for {len(self.monitored_tables)} tables")
    
    def register_handler(self, table_name: str, handler_function):
        """注册表变更处理器"""
        self.change_handlers[table_name] = handler_function
        logger.info(f"Registered handler for table: {table_name}")
    
    def check_changes(self) -> List[ChangeEvent]:
        """检查数据库变更"""
        changes = []
        current_time = datetime.now()
        
        with self._lock:
            for table_name, config in self.monitored_tables.items():
                try:
                    table_changes = self._check_table_changes(
                        table_name, 
                        config,
                        self.last_check_time,
                        current_time
                    )
                    changes.extend(table_changes)
                except Exception as e:
                    logger.error(f"Error checking changes for table {table_name}: {e}")
            
            self.last_check_time = current_time
        
        return changes
    
    def _check_table_changes(self, table_name: str, config: Dict, 
                           since: datetime, until: datetime) -> List[ChangeEvent]:
        """检查单个表的变更"""
        changes = []
        
        # 这里使用简化的变更检测方法
        # 实际项目中可能需要使用 MySQL binlog、触发器或时间戳字段
        
        if table_name == "derived_intl_teacher_data":
            changes.extend(self._check_teacher_changes(config, since, until))
        elif table_name == "data_intl_wide_view":
            changes.extend(self._check_teacher_wide_changes(config, since, until))
        
        return changes
    
    def _check_teacher_changes(self, config: Dict, since: datetime, until: datetime) -> List[ChangeEvent]:
        """检查 teacher 表变更"""
        changes = []
        
        try:
            with get_session() as session:
                # 假设表有 updated_at 字段
                # 这里模拟检查最近的记录
                from talent_platform.db.models import Teacher
                
                statement = select(Teacher).order_by(desc(Teacher.id)).limit(10)
                recent_teachers = session.exec(statement).all()
                
                for teacher in recent_teachers:
                    # 简化的变更检测逻辑
                    # 实际应该基于 updated_at 或其他时间戳字段
                    change = ChangeEvent(
                        table_name="derived_intl_teacher_data",
                        operation="UPDATE",
                        record_id=teacher.teacher_id,
                        timestamp=datetime.now(),
                        new_data={
                            "teacher_id": teacher.teacher_id,
                            "school_name": teacher.school_name,
                            "derived_teacher_name": teacher.derived_teacher_name,
                            "is_valid": teacher.is_valid
                        },
                        trigger_plugins=config.get("triggers", [])
                    )
                    
                    # 检查条件
                    if self._check_conditions(change.new_data, config.get("conditions", {})):
                        changes.append(change)
                        
        except Exception as e:
            logger.error(f"Error checking teacher changes: {e}")
        
        return changes
    
    def _check_teacher_wide_changes(self, config: Dict, since: datetime, until: datetime) -> List[ChangeEvent]:
        """检查 teacher_wide 表变更"""
        changes = []
        
        try:
            with get_session() as session:
                from talent_platform.db.models import TeacherWide
                
                statement = select(TeacherWide).limit(5)  # 简化示例
                recent_records = session.exec(statement).all()
                
                for record in recent_records:
                    change = ChangeEvent(
                        table_name="data_intl_wide_view",
                        operation="UPDATE",
                        record_id=record.teacher_id,
                        timestamp=datetime.now(),
                        new_data={
                            "teacher_id": record.teacher_id,
                            "school_name": record.school_name,
                            "derived_teacher_name": record.derived_teacher_name,
                        },
                        trigger_plugins=config.get("triggers", [])
                    )
                    
                    if self._check_conditions(change.new_data, config.get("conditions", {})):
                        changes.append(change)
                        
        except Exception as e:
            logger.error(f"Error checking teacher wide changes: {e}")
        
        return changes
    
    def _check_conditions(self, data: Dict, conditions: Dict) -> bool:
        """检查变更是否符合触发条件"""
        if not conditions:
            return True
        
        for key, expected_value in conditions.items():
            if key not in data or data[key] != expected_value:
                return False
        
        return True
    
    def process_changes(self, changes: List[ChangeEvent]):
        """处理变更事件"""
        for change in changes:
            logger.info(f"Processing change: {change.table_name} - {change.operation} - {change.record_id}")
            
            # 调用注册的处理器
            if change.table_name in self.change_handlers:
                try:
                    self.change_handlers[change.table_name](change)
                except Exception as e:
                    logger.error(f"Error in change handler for {change.table_name}: {e}")
            
            # 触发插件执行
            from talent_platform.scheduler.tasks import execute_plugin_task
            for plugin_name in change.trigger_plugins:
                try:
                    # 异步执行插件任务
                    execute_plugin_task.delay(
                        plugin_name=plugin_name,
                        change_event=change.__dict__
                    )
                    logger.info(f"Triggered plugin {plugin_name} for change {change.record_id}")
                except Exception as e:
                    logger.error(f"Error triggering plugin {plugin_name}: {e}")


# 全局数据库监听器实例
db_monitor = DatabaseMonitor() 