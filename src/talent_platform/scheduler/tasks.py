from celery import Task
from typing import Dict, Any, Optional
import traceback
from datetime import datetime

from .celery_app import celery_app
from .plugin_manager import plugin_manager
from .db_monitor import db_monitor
from talent_platform.logger import logger


class CallbackTask(Task):
    """带回调的任务基类"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Traceback: {einfo}")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def execute_plugin_task(self, plugin_name: str, change_event: Optional[Dict] = None, **kwargs):
    """执行插件任务"""
    try:
        logger.info(f"Executing plugin task: {plugin_name}")
        
        # 准备插件参数
        plugin_kwargs = kwargs.copy()
        if change_event:
            plugin_kwargs['change_event'] = change_event
        
        # 执行插件
        result = plugin_manager.execute_plugin(plugin_name, **plugin_kwargs)
        
        logger.info(f"Plugin {plugin_name} executed successfully")
        return {
            "status": "success",
            "plugin_name": plugin_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Plugin {plugin_name} execution failed: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying plugin {plugin_name} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60)
        
        # 最终失败
        return {
            "status": "failed",
            "plugin_name": plugin_name,
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }

@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def execute_chain_plugin_task(self, previous_result: Dict[str, Any], plugin_name: str, change_event: Optional[Dict] = None, **kwargs):
    """执行链式插件任务，明确接收上一个任务的返回结果。"""
    try:
        logger.info(f"Executing chained plugin task: {plugin_name}")
        
        # 准备插件参数，从上一个任务的结果开始
        plugin_kwargs = {}

        # 合并任何在签名中额外定义的kwargs
        plugin_kwargs.update(kwargs)

        if change_event:
            plugin_kwargs['change_event'] = change_event
        
        # 执行插件
        result = plugin_manager.execute_plugin(plugin_name, **plugin_kwargs)
        
        logger.info(f"Plugin {plugin_name} executed successfully")
        return {
            "status": "success",
            "plugin_name": plugin_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Plugin {plugin_name} execution failed: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying plugin {plugin_name} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60)
        
        # 最终失败
        return {
            "status": "failed",
            "plugin_name": plugin_name,
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, base=CallbackTask)
def monitor_db_changes(self):
    """监听数据库变更任务"""
    try:
        logger.info("Checking database changes...")
        
        # 检查变更
        changes = db_monitor.check_changes()
        
        if changes:
            logger.info(f"Found {len(changes)} database changes")
            
            # 处理变更
            db_monitor.process_changes(changes)
            
            return {
                "status": "success",
                "changes_count": len(changes),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.debug("No database changes detected")
            return {
                "status": "success",
                "changes_count": 0,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as exc:
        logger.error(f"Database monitoring failed: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, base=CallbackTask)
def batch_execute_plugins(self, plugin_configs: list):
    """批量执行插件任务"""
    try:
        results = []
        
        for config in plugin_configs:
            plugin_name = config.get("plugin_name")
            parameters = config.get("parameters", {})
            
            try:
                result = plugin_manager.execute_plugin(plugin_name, **parameters)
                results.append({
                    "plugin_name": plugin_name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                logger.error(f"Batch plugin {plugin_name} failed: {e}")
                results.append({
                    "plugin_name": plugin_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "status": "completed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch plugin execution failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, base=CallbackTask)
def schedule_plugin_execution(self, plugin_name: str, cron_expression: str, parameters: Dict = None):
    """调度插件执行"""
    try:
        if parameters is None:
            parameters = {}
        
        # 这里可以集成 cron 解析和调度逻辑
        # 暂时简化实现
        result = execute_plugin_task.delay(plugin_name, **parameters)
        
        return {
            "status": "scheduled",
            "plugin_name": plugin_name,
            "task_id": result.id,
            "cron_expression": cron_expression,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Plugin scheduling failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, base=CallbackTask)
def plugin_health_check(self):
    """插件健康检查"""
    try:
        plugins = plugin_manager.list_plugins()
        health_status = []
        
        for plugin in plugins:
            plugin_name = plugin["name"]
            if plugin["enabled"]:
                try:
                    # 尝试加载插件
                    module = plugin_manager.load_plugin(plugin_name)
                    status = "healthy" if module else "unhealthy"
                except Exception as e:
                    status = "error"
                    logger.error(f"Plugin {plugin_name} health check failed: {e}")
            else:
                status = "disabled"
            
            health_status.append({
                "plugin_name": plugin_name,
                "status": status,
                "version": plugin["version"]
            })
        
        return {
            "status": "completed",
            "plugins": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Plugin health check failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        } 