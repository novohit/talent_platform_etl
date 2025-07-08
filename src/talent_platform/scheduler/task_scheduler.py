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
        """加载调度任务配置"""
        # 这里可以从数据库或配置文件加载
        # 示例配置
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
            }
        ]
        
        for task_config in default_tasks:
            task = ScheduledTask(**task_config)
            self.scheduled_tasks[task.id] = task
        
        logger.info(f"Loaded {len(self.scheduled_tasks)} scheduled tasks")
    
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
        """添加调度任务"""
        task = ScheduledTask(**task_config)
        self.scheduled_tasks[task.id] = task
        
        logger.info(f"Added scheduled task: {task.name}")
        return task.id
    
    def remove_scheduled_task(self, task_id: str) -> bool:
        """移除调度任务"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Removed scheduled task: {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = True
            logger.info(f"Enabled task: {task_id}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = False
            logger.info(f"Disabled task: {task_id}")
            return True
        return False
    
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