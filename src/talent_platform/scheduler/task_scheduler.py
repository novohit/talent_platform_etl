import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .tasks import (
    execute_plugin_task, 
    batch_execute_plugins, 
    schedule_plugin_execution,
    plugin_health_check
)
from .plugin_manager import plugin_manager
from .db_monitor import db_monitor
from talent_platform.logger import logger


@dataclass
class ScheduledTask:
    """调度任务定义"""
    id: str
    name: str
    plugin_name: str
    parameters: Dict[str, Any]
    schedule_type: str  # 'cron', 'interval', 'once', 'trigger'
    schedule_config: Dict[str, Any]  # cron表达式、间隔时间等
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_history: List[Dict] = []
        
        # 初始化
        self._load_scheduled_tasks()
        self._register_db_handlers()
    
    def _load_scheduled_tasks(self):
        """加载调度任务配置 - 从数据库加载持久化任务"""
        logger.info("Loading persisted scheduled tasks...")
        
        # 从数据库加载所有持久化任务
        loaded_count = self.load_persisted_tasks()
        
        # 如果数据库为空，创建一些默认任务
        # if loaded_count == 0:
        #     logger.info("No persisted tasks found, creating default tasks...")
        #     self._create_default_tasks()
        
        logger.info(f"Task scheduler initialization completed with {len(self.scheduled_tasks)} tasks")
    
    def _create_default_tasks(self):
        """创建默认的调度任务"""
        # 示例默认任务配置
        default_tasks = [
            {
                "id": "daily_teacher_sync",
                "name": "每日教师数据同步",
                "plugin_name": "data_processor",
                "parameters": {"sync_type": "daily"},
                "schedule_type": "cron",
                "schedule_config": {"cron": "0 2 * * *"}  # 每天凌晨2点
            },
            {
                "id": "hourly_es_update",
                "name": "每小时ES索引更新",
                "plugin_name": "es_indexer",
                "parameters": {"batch_size": 100},
                "schedule_type": "interval",
                "schedule_config": {"interval": 3600}  # 每小时
            },
            {
                "id": "mysql_health_check",
                "name": "MySQL数据库健康检查",
                "plugin_name": "mysql_test",
                "parameters": {"operation": "health_check"},
                "schedule_type": "interval",
                "schedule_config": {"interval": 300}  # 每5分钟
            },
            {
                "id": "mysql_daily_test",
                "name": "MySQL每日连接测试",
                "plugin_name": "mysql_test",
                "parameters": {"operation": "query_test"},
                "schedule_type": "cron",
                "schedule_config": {"cron": "0 8 * * *"}  # 每天早上8点
            }
        ]
        
        # 使用 add_scheduled_task 方法来创建默认任务（自动持久化）
        for task_config in default_tasks:
            try:
                self.add_scheduled_task(task_config)
                logger.info(f"Created default task: {task_config['id']}")
            except Exception as e:
                logger.error(f"Failed to create default task {task_config['id']}: {e}")
        
        logger.info(f"Default tasks creation completed")
    
    def _register_db_handlers(self):
        """注册数据库变更处理器"""
        def handle_teacher_change(change_event):
            """处理教师数据变更"""
            logger.info(f"Handling teacher change: {change_event.record_id}")
            
            # 根据变更类型触发不同的处理
            if change_event.operation == "INSERT":
                self.trigger_plugin("data_processor", {
                    "operation": "process_new_teacher",
                    "teacher_id": change_event.record_id,
                    "data": change_event.new_data
                })
            elif change_event.operation == "UPDATE":
                self.trigger_plugin("es_indexer", {
                    "operation": "update_teacher_index",
                    "teacher_id": change_event.record_id,
                    "data": change_event.new_data
                })
        
        def handle_teacher_wide_change(change_event):
            """处理教师宽表数据变更"""
            logger.info(f"Handling teacher wide change: {change_event.record_id}")
            
            self.trigger_plugin("teacher_analyzer", {
                "operation": "analyze_teacher",
                "teacher_id": change_event.record_id,
                "data": change_event.new_data
            })
        
        # 注册处理器
        db_monitor.register_handler("derived_intl_teacher_data", handle_teacher_change)
        db_monitor.register_handler("data_intl_wide_view", handle_teacher_wide_change)
    
    def add_scheduled_task(self, task_config: Dict) -> str:
        """添加调度任务 - 纯 Celery Beat + 持久化方案"""
        from .celery_app import celery_app
        from celery.schedules import crontab
        from ..db.database import get_scheduler_db_session
        from ..db.models import ScheduledTaskModel
        from datetime import datetime
        
        task = ScheduledTask(**task_config)
        
        # 构建 Celery 调度配置
        schedule = self._build_celery_schedule(task.schedule_type, task.schedule_config)
        
        if schedule is None:
            raise ValueError(f"Invalid schedule configuration: {task.schedule_config}")
        
        try:
            # 1. 持久化到数据库
            with get_scheduler_db_session() as session:
                # 检查任务是否已存在
                existing_task = session.get(ScheduledTaskModel, task.id)
                if existing_task:
                    # 更新现有任务
                    existing_task.name = task.name
                    existing_task.plugin_name = task.plugin_name
                    existing_task.parameters = task.parameters
                    existing_task.schedule_type = task.schedule_type
                    existing_task.schedule_config = task.schedule_config
                    existing_task.enabled = task.enabled
                    existing_task.updated_at = datetime.now()
                    session.add(existing_task)
                else:
                    # 创建新任务
                    db_task = ScheduledTaskModel(
                        id=task.id,
                        name=task.name,
                        plugin_name=task.plugin_name,
                        parameters=task.parameters,
                        schedule_type=task.schedule_type,
                        schedule_config=task.schedule_config,
                        enabled=task.enabled,
                        description=task_config.get("description"),
                        tags=task_config.get("tags"),
                        priority=task_config.get("priority", 5),
                        max_retries=task_config.get("max_retries", 3),
                        timeout=task_config.get("timeout")
                    )
                    session.add(db_task)
                
                session.commit()
                logger.info(f"Persisted task to database: {task.id}")
            
            # 2. 添加到 Celery Beat Schedule
            self._add_task_to_celery_beat(task, schedule)
            
            # 3. 存储到内存（TODO 后续更换成分布式缓存）
            self.scheduled_tasks[task.id] = task
            
            logger.info(f"Successfully added scheduled task: {task.name}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to add scheduled task {task.id}: {e}")
            raise
    
    def _build_celery_schedule(self, schedule_type: str, schedule_config: Dict):
        """构建 Celery 调度配置"""
        from celery.schedules import crontab
        
        if schedule_type == "interval":
            interval = schedule_config.get("interval", 3600)
            return float(interval)
        
        elif schedule_type == "cron":
            cron_expr = schedule_config.get("cron", "0 * * * *")
            # 解析 cron 表达式: "minute hour day_of_month month day_of_week"
            parts = cron_expr.split()
            
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expr}")
                return None
            
            try:
                return crontab(
                    minute=parts[0],
                    hour=parts[1], 
                    day_of_month=parts[2],
                    month_of_year=parts[3],
                    day_of_week=parts[4]
                )
            except Exception as e:
                logger.error(f"Failed to parse cron expression {cron_expr}: {e}")
                return None
        
        else:
            logger.error(f"Unsupported schedule type: {schedule_type}")
            return None
    
    def _add_task_to_celery_beat(self, task: ScheduledTask, schedule):
        """添加任务到 Celery Beat Schedule"""
        from .celery_app import celery_app
        
        if not task.enabled:
            logger.info(f"Task {task.id} is disabled, skipping Celery Beat registration")
            return
        
        try:
            # 构建任务配置
            task_config = {
                'task': 'talent_platform.scheduler.tasks.execute_plugin_task',
                'schedule': schedule,
                'args': [task.plugin_name],
                'kwargs': task.parameters,
                'options': {
                    'queue': 'plugin_tasks',
                    'priority': getattr(task, 'priority', 5),
                }
            }
            
            # 如果有超时设置
            if hasattr(task, 'timeout') and task.timeout:
                task_config['options']['time_limit'] = task.timeout
            
            # 如果有重试设置
            if hasattr(task, 'max_retries'):
                task_config['options']['retry'] = True
                task_config['options']['max_retries'] = task.max_retries
            
            # 动态添加到 Celery Beat
            celery_app.conf.beat_schedule[task.id] = task_config
            
            logger.info(f"Added task {task.id} to Celery Beat schedule")
            
        except Exception as e:
            logger.error(f"Failed to add task {task.id} to Celery Beat: {e}")
            raise
    
    def _remove_task_from_celery_beat(self, task_id: str):
        """从 Celery Beat Schedule 移除任务"""
        from .celery_app import celery_app
        
        try:
            if task_id in celery_app.conf.beat_schedule:
                del celery_app.conf.beat_schedule[task_id]
                logger.info(f"Removed task {task_id} from Celery Beat schedule")
                return True
            else:
                logger.warning(f"Task {task_id} not found in Celery Beat schedule")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove task {task_id} from Celery Beat: {e}")
            return False
    
    def remove_scheduled_task(self, task_id: str) -> bool:
        """移除调度任务 - 从数据库和 Celery Beat 中删除"""
        from ..db.database import get_scheduler_db_session
        from ..db.models import ScheduledTaskModel
        
        try:
            # 1. 从数据库删除
            with get_scheduler_db_session() as session:
                db_task = session.get(ScheduledTaskModel, task_id)
                if db_task:
                    session.delete(db_task)
                    session.commit()
                    logger.info(f"Deleted task from database: {task_id}")
                else:
                    logger.warning(f"Task {task_id} not found in database")
            
            # 2. 从 Celery Beat 移除
            self._remove_task_from_celery_beat(task_id)
            
            # 3. 从内存移除
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
            
            logger.info(f"✅ Successfully removed scheduled task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove scheduled task {task_id}: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务 - 更新数据库和 Celery Beat"""
        from ..db.database import get_scheduler_db_session
        from ..db.models import ScheduledTaskModel
        from datetime import datetime
        
        try:
            # 1. 更新数据库状态
            with get_scheduler_db_session() as session:
                db_task = session.get(ScheduledTaskModel, task_id)
                if not db_task:
                    logger.error(f"Task {task_id} not found in database")
                    return False
                
                db_task.enabled = True
                db_task.updated_at = datetime.now()
                session.add(db_task)
                session.commit()
                logger.info(f"Enabled task in database: {task_id}")
            
            # 2. 更新内存状态
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].enabled = True
            
            # 3. 重新添加到 Celery Beat
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                schedule = self._build_celery_schedule(task.schedule_type, task.schedule_config)
                if schedule:
                    self._add_task_to_celery_beat(task, schedule)
            
            logger.info(f"✅ Successfully enabled task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to enable task {task_id}: {e}")
            return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务 - 更新数据库和 Celery Beat"""
        from ..db.database import get_scheduler_db_session
        from ..db.models import ScheduledTaskModel
        from datetime import datetime
        
        try:
            # 1. 更新数据库状态
            with get_scheduler_db_session() as session:
                db_task = session.get(ScheduledTaskModel, task_id)
                if not db_task:
                    logger.error(f"Task {task_id} not found in database")
                    return False
                
                db_task.enabled = False
                db_task.updated_at = datetime.now()
                session.add(db_task)
                session.commit()
                logger.info(f"Disabled task in database: {task_id}")
            
            # 2. 更新内存状态
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].enabled = False
            
            # 3. 从 Celery Beat 移除
            self._remove_task_from_celery_beat(task_id)
            
            logger.info(f"Successfully disabled task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable task {task_id}: {e}")
            return False
    
    def load_persisted_tasks(self):
        """从数据库加载持久化的定时任务"""
        from ..db.database import get_scheduler_db_session
        from ..db.models import ScheduledTaskModel
        
        try:
            with get_scheduler_db_session() as session:
                # 查询所有任务
                db_tasks = session.query(ScheduledTaskModel).all()
                
                loaded_count = 0
                enabled_count = 0
                
                for db_task in db_tasks:
                    try:
                        # 转换为 ScheduledTask 对象
                        task = ScheduledTask(
                            id=db_task.id,
                            name=db_task.name,
                            plugin_name=db_task.plugin_name,
                            parameters=db_task.parameters,
                            schedule_type=db_task.schedule_type,
                            schedule_config=db_task.schedule_config,
                            enabled=db_task.enabled,
                            last_run=db_task.last_run,
                            next_run=db_task.next_run,
                            created_at=db_task.created_at
                        )
                        
                        # 存储到内存
                        self.scheduled_tasks[task.id] = task
                        loaded_count += 1
                        
                        # 如果任务启用，添加到 Celery Beat
                        if task.enabled:
                            schedule = self._build_celery_schedule(task.schedule_type, task.schedule_config)
                            if schedule:
                                self._add_task_to_celery_beat(task, schedule)
                                enabled_count += 1
                        
                        logger.debug(f"Loaded task: {task.id} (enabled: {task.enabled})")
                        
                    except Exception as e:
                        logger.error(f"Failed to load task {db_task.id}: {e}")
                        continue
                
                logger.info(f"Loaded {loaded_count} tasks from database ({enabled_count} enabled)")
                return loaded_count
                
        except Exception as e:
            logger.error(f"Failed to load persisted tasks: {e}")
            return 0
    
    def trigger_plugin(self, plugin_name: str, parameters: Dict = None, priority: str = "normal") -> str:
        """立即触发插件执行"""
        if parameters is None:
            parameters = {}
        
        # 检查插件是否存在
        if not plugin_manager.get_plugin_metadata(plugin_name):
            raise ValueError(f"Plugin {plugin_name} not found")
        
        # 根据优先级选择队列
        queue = "high_priority" if priority == "high" else "plugin_tasks"
        
        # 异步执行
        result = execute_plugin_task.apply_async(
            args=[plugin_name],
            kwargs=parameters,
            queue=queue
        )
        
        # 记录任务历史
        self.task_history.append({
            "task_id": result.id,
            "plugin_name": plugin_name,
            "parameters": parameters,
            "triggered_at": datetime.now().isoformat(),
            "trigger_type": "manual",
            "status": "queued"
        })
        
        logger.info(f"Triggered plugin {plugin_name} with task ID: {result.id}")
        return result.id
    
    def batch_trigger_plugins(self, plugin_configs: List[Dict]) -> str:
        """批量触发插件执行"""
        result = batch_execute_plugins.delay(plugin_configs)
        
        self.task_history.append({
            "task_id": result.id,
            "plugin_count": len(plugin_configs),
            "triggered_at": datetime.now().isoformat(),
            "trigger_type": "batch",
            "status": "queued"
        })
        
        logger.info(f"Triggered batch execution of {len(plugin_configs)} plugins")
        return result.id
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        from .celery_app import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None
        }
    
    def get_scheduled_tasks(self) -> List[Dict]:
        """获取所有调度任务"""
        return [asdict(task) for task in self.scheduled_tasks.values()]
    
    def get_task_history(self, limit: int = 100) -> List[Dict]:
        """获取任务历史"""
        return self.task_history[-limit:]
    
    def get_plugin_metrics(self) -> Dict:
        """获取插件执行指标"""
        from collections import defaultdict
        
        metrics = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_execution": None
        })
        
        for record in self.task_history:
            plugin_name = record.get("plugin_name", "unknown")
            status = record.get("status", "unknown")
            
            metrics[plugin_name]["total_executions"] += 1
            if status == "success":
                metrics[plugin_name]["successful_executions"] += 1
            elif status == "failed":
                metrics[plugin_name]["failed_executions"] += 1
            
            # 更新最后执行时间
            triggered_at = record.get("triggered_at")
            if triggered_at:
                if (not metrics[plugin_name]["last_execution"] or 
                    triggered_at > metrics[plugin_name]["last_execution"]):
                    metrics[plugin_name]["last_execution"] = triggered_at
        
        # 计算成功率
        for plugin_name, stats in metrics.items():
            total = stats["total_executions"]
            successful = stats["successful_executions"]
            stats["success_rate"] = (successful / total * 100) if total > 0 else 0
        
        return dict(metrics)
    
    def health_check(self) -> Dict:
        """系统健康检查"""
        # 执行插件健康检查任务
        result = plugin_health_check.delay()
        
        # 收集系统状态
        status = {
            "scheduler_status": "running",
            "total_plugins": len(plugin_manager.plugins),
            "enabled_plugins": len([p for p in plugin_manager.plugins.values() if p.enabled]),
            "scheduled_tasks": len(self.scheduled_tasks),
            "active_tasks": len([t for t in self.scheduled_tasks.values() if t.enabled]),
            "health_check_task_id": result.id,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    def export_config(self) -> Dict:
        """导出调度配置"""
        config = {
            "scheduled_tasks": [asdict(task) for task in self.scheduled_tasks.values()],
            "plugins": plugin_manager.list_plugins(),
            "exported_at": datetime.now().isoformat()
        }
        
        return config
    
    def import_config(self, config: Dict):
        """导入调度配置"""
        if "scheduled_tasks" in config:
            for task_config in config["scheduled_tasks"]:
                task = ScheduledTask(**task_config)
                self.scheduled_tasks[task.id] = task
            
            logger.info(f"Imported {len(config['scheduled_tasks'])} scheduled tasks")
    



# 全局任务调度器实例
task_scheduler = TaskScheduler() 