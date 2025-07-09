"""
基础消费者类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from .canal_client import ChangeEvent
from talent_platform.logger import logger


@dataclass
class TableFilter:
    """表过滤器配置"""
    database: str
    table: str
    event_types: Set[str] = None  # INSERT, UPDATE, DELETE
    
    def __post_init__(self):
        if self.event_types is None:
            self.event_types = {'INSERT', 'UPDATE', 'DELETE'}
    
    def matches(self, event: ChangeEvent) -> bool:
        """检查事件是否匹配过滤器"""
        return (event.database == self.database and 
                event.table == self.table and 
                event.event_type in self.event_types)


class BaseConsumer(ABC):
    """基础消费者类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.filters: List[TableFilter] = []
        self._task_scheduler = None
    
    @property
    def task_scheduler(self):
        """获取任务调度器实例"""
        if self._task_scheduler is None:
            from talent_platform.scheduler.task_scheduler import task_scheduler
            self._task_scheduler = task_scheduler
        return self._task_scheduler
    
    def add_filter(self, database: str, table: str, event_types: Set[str] = None):
        """添加表过滤器"""
        filter_obj = TableFilter(database, table, event_types)
        self.filters.append(filter_obj)
        logger.info(f"Consumer {self.name} added filter: {database}.{table} - {event_types or 'ALL'}")
    
    def remove_filter(self, database: str, table: str):
        """移除表过滤器"""
        self.filters = [f for f in self.filters if not (f.database == database and f.table == table)]
        logger.info(f"Consumer {self.name} removed filter: {database}.{table}")
    
    def should_handle(self, event: ChangeEvent) -> bool:
        """检查是否应该处理该事件"""
        if not self.enabled:
            return False
        
        # 如果没有过滤器，处理所有事件
        if not self.filters:
            return True
        
        # 检查是否匹配任何过滤器
        return any(filter_obj.matches(event) for filter_obj in self.filters)
    
    def handle_event(self, event: ChangeEvent):
        """处理数据库变更事件（入口方法）"""
        if not self.should_handle(event):
            return
        
        try:
            logger.debug(f"Consumer {self.name} handling event: {event.database}.{event.table} - {event.event_type}")
            self.process_event(event)
        except Exception as e:
            logger.error(f"Consumer {self.name} failed to process event: {e}")
            self.on_error(event, e)
    
    @abstractmethod
    def process_event(self, event: ChangeEvent):
        """处理具体的数据库变更事件（子类实现）"""
        pass
    
    def on_error(self, event: ChangeEvent, error: Exception):
        """错误处理（子类可重写）"""
        logger.error(f"Consumer {self.name} error processing {event.database}.{event.table}: {error}")
    
    def trigger_plugin(self, plugin_name: str, parameters: Dict[str, Any] = None, priority: str = "normal") -> str:
        """触发插件执行"""
        if parameters is None:
            parameters = {}
        
        try:
            task_id = self.task_scheduler.trigger_plugin(plugin_name, parameters, priority)
            logger.info(f"Consumer {self.name} triggered plugin {plugin_name}, task_id: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Consumer {self.name} failed to trigger plugin {plugin_name}: {e}")
            raise
    
    def enable(self):
        """启用消费者"""
        self.enabled = True
        logger.info(f"Consumer {self.name} enabled")
    
    def disable(self):
        """禁用消费者"""
        self.enabled = False
        logger.info(f"Consumer {self.name} disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """获取消费者状态"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'filters': [
                {
                    'database': f.database,
                    'table': f.table,
                    'event_types': list(f.event_types)
                }
                for f in self.filters
            ]
        } 