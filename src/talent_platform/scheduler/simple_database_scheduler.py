"""
简洁数据库调度器 - 重新设计版本
核心理念：简单、可靠、高效
"""

import time
import hashlib
from datetime import datetime
from celery import schedules
from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab
from celery.utils.log import get_logger
from typing import Dict, Any, Optional

from ..db.database import get_scheduler_db_session
from ..db.models import ScheduledTaskModel
from .tasks import execute_plugin_task

logger = get_logger(__name__)


class SimpleDatabaseScheduleEntry(ScheduleEntry):
    """简单数据库调度条目"""
    
    def __init__(self, model=None, app=None, **kwargs):
        self.model = model
        self.app = app
        
        if model:
            # 构建Celery调度对象
            schedule = self._build_schedule(model.schedule_type, model.schedule_config)
            
            # 构建任务签名
            task = execute_plugin_task.s(model.plugin_name, **model.parameters)
            
            # 构建选项
            options = {
                'queue': 'plugin_tasks',
                'priority': model.priority or 5,
            }
            
            if model.timeout:
                options['time_limit'] = model.timeout
            if model.max_retries:
                options['retry'] = True
                options['max_retries'] = model.max_retries
            
            # 调用父类构造函数
            super().__init__(
                name=model.id,
                task=task,
                schedule=schedule,
                args=(),
                kwargs={},
                options=options,
                last_run_at=model.last_run,
                total_run_count=0,
                app=app
            )
        else:
            # 从kwargs构建
            super().__init__(**kwargs)
    
    def _build_schedule(self, schedule_type: str, schedule_config: Dict[str, Any]):
        """构建Celery调度对象"""
        if schedule_type == 'interval':
            return schedules.schedule(
                run_every=schedule_config.get('interval', 60)
            )
        elif schedule_type == 'cron':
            return crontab(
                minute=schedule_config.get('minute', '*'),
                hour=schedule_config.get('hour', '*'),
                day_of_week=schedule_config.get('day_of_week', '*'),
                day_of_month=schedule_config.get('day_of_month', '*'),
                month_of_year=schedule_config.get('month_of_year', '*')
            )
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
    
    def __next__(self):
        """执行任务并更新数据库"""
        # 执行任务
        result = super().__next__()
        
        # 更新数据库的last_run时间
        if self.model:
            try:
                with get_scheduler_db_session() as session:
                    db_task = session.get(ScheduledTaskModel, self.model.id)
                    if db_task:
                        db_task.last_run = datetime.now()
                        session.add(db_task)
                        session.commit()
                        logger.debug(f"Updated last_run for task: {self.model.id}")
            except Exception as e:
                logger.error(f"Failed to update last_run for task {self.model.id}: {e}")
        
        return result


class SimpleDatabaseScheduler(Scheduler):
    """简洁数据库调度器"""
    
    Entry = SimpleDatabaseScheduleEntry
    
    def __init__(self, *args, **kwargs):
        # 初始化状态跟踪
        self._last_sync_time = None
        self._last_tasks_hash = None
        self._schedule_cache = {}
        
        super().__init__(*args, **kwargs)
        
        logger.info("SimpleDatabaseScheduler initialized")
    
    def setup_schedule(self):
        """初始化调度表"""
        self.update_schedule()
        logger.info("Database schedule setup completed")
    
    def update_schedule(self):
        """更新调度表"""
        new_schedule = self.all_as_schedule()
        self._schedule_cache = new_schedule
        logger.info(f"Schedule updated with {len(new_schedule)} tasks")
    
    @property
    def schedule(self):
        """获取当前调度表（带缓存和变更检测）"""
        # 检查是否需要更新
        if self.should_sync():
            self.update_schedule()
        
        return self._schedule_cache
    
    def should_sync(self):
        """检查是否需要同步数据库"""
        now = time.time()
        
        # 初次加载
        if self._last_sync_time is None:
            self._last_sync_time = now
            return True
        
        # 每30秒检查一次变化
        if now - self._last_sync_time < 30:
            return False
        
        self._last_sync_time = now
        
        # 计算当前任务哈希值
        current_hash = self._calculate_tasks_hash()
        
        # 比较哈希值
        if current_hash != self._last_tasks_hash:
            logger.info(f"Tasks changed detected: {self._last_tasks_hash} -> {current_hash}")
            self._last_tasks_hash = current_hash
            return True
        
        return False
    
    def _calculate_tasks_hash(self):
        """计算当前所有启用任务的哈希值"""
        try:
            with get_scheduler_db_session() as session:
                tasks = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.enabled == True
                ).order_by(ScheduledTaskModel.id).all()
                
                # 构建用于哈希的数据
                hash_data = []
                for task in tasks:
                    task_data = {
                        'id': task.id,
                        'name': task.name,
                        'plugin_name': task.plugin_name,
                        'parameters': task.parameters,
                        'schedule_type': task.schedule_type,
                        'schedule_config': task.schedule_config,
                        'enabled': task.enabled,
                        'priority': task.priority,
                        'max_retries': task.max_retries,
                        'timeout': task.timeout,
                        'updated_at': task.updated_at.isoformat() if task.updated_at else None
                    }
                    hash_data.append(str(sorted(task_data.items())))
                
                # 计算MD5哈希
                content = '|'.join(hash_data)
                return hashlib.md5(content.encode()).hexdigest()
                
        except Exception as e:
            logger.error(f"Failed to calculate tasks hash: {e}")
            return str(time.time())  # 返回时间戳作为fallback
    
    def all_as_schedule(self):
        """从数据库加载所有启用的任务"""
        schedule_dict = {}
        
        try:
            with get_scheduler_db_session() as session:
                enabled_tasks = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.enabled == True
                ).all()
                
                for task in enabled_tasks:
                    try:
                        entry = self.Entry(model=task, app=self.app)
                        schedule_dict[task.id] = entry
                        logger.debug(f"Loaded task: {task.id}")
                    except Exception as e:
                        logger.error(f"Failed to create entry for task {task.id}: {e}")
                
                logger.info(f"Loaded {len(schedule_dict)} enabled tasks from database")
                
        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
        
        return schedule_dict
    
    def reserve(self, entry):
        """保留任务执行时间"""
        new_entry = super().reserve(entry)
        return new_entry
    
    def apply_async(self, entry, publisher=None, **kwargs):
        """应用异步任务"""
        return super().apply_async(entry, publisher, **kwargs) 