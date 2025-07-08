from celery import Celery
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
        'talent_platform.scheduler.tasks.monitor_db_changes': {'queue': 'monitoring'},
    },
    
    # 工作池配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 结果过期时间
    result_expires=3600,
    
    # 重试配置
    task_reject_on_worker_lost=True,
    
    # 定时任务配置
    beat_schedule={
        'monitor-db-changes': {
            'task': 'talent_platform.scheduler.tasks.monitor_db_changes',
            'schedule': config.DB_CHANGE_POLLING_INTERVAL,
        },
    },
)

logger.info(f"Celery app initialized with broker: {config.CELERY_BROKER_URL}") 