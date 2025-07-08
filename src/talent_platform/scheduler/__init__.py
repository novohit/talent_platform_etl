from .celery_app import celery_app
from .task_scheduler import TaskScheduler
from .plugin_manager import PluginManager

# 初始化并启用热加载
def initialize_scheduler():
    """初始化调度系统"""
    from .plugin_manager import plugin_manager
    from .task_scheduler import task_scheduler
    
    # 启用插件热加载
    try:
        plugin_manager.enable_hot_loading()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to enable hot loading: {e}")
    
    return plugin_manager, task_scheduler

# 自动初始化
plugin_manager, task_scheduler = initialize_scheduler()

__all__ = ["celery_app", "TaskScheduler", "PluginManager", "plugin_manager", "task_scheduler"] 