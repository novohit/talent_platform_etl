from celery import Celery
from celery.schedules import crontab
from talent_platform.config import config
from talent_platform.logger import logger

# 创建 Celery 应用
celery_app = Celery(
    'talent_platform_scheduler',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['talent_platform.scheduler.tasks']
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务路由配置
    task_routes={
        'talent_platform.scheduler.tasks.execute_plugin_task': {'queue': 'plugin_tasks'},
        'talent_platform.scheduler.tasks.execute_chain_plugin_task': {'queue': 'plugin_tasks'},
        'talent_platform.scheduler.tasks.monitor_db_changes': {'queue': 'monitoring'},
    },
    
    # 工作池配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 结果过期时间
    result_expires=3600,
    
    # 重试配置
    task_reject_on_worker_lost=True,
    
    # 使用数据库调度器
    beat_scheduler='talent_platform.scheduler.simple_database_scheduler:SimpleDatabaseScheduler',
    
    # 数据库调度器设置 - 控制调度器唤醒频率以检测变化
    beat_max_loop_interval=5.0,  # 每5秒检查一次（而非强制同步）
    
    # 静态任务配置（可选，用于系统级任务）
    beat_schedule={
        # 系统监控任务（如果需要的话）
        # 'monitor-db-changes': {
        #     'task': 'talent_platform.scheduler.tasks.monitor_db_changes',
        #     'schedule': config.DB_CHANGE_POLLING_INTERVAL,
        # },
    },
)

logger.info(f"Celery app initialized with broker: {config.CELERY_BROKER_URL}") 