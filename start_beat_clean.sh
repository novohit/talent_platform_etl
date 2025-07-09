#!/bin/bash
#
# 清洁启动 Celery Beat（最小日志输出）
# 只显示关键信息
#

echo "🚀 启动 Celery Beat - 清洁模式"
echo "==============================="

# 关闭 SQL 日志
export SQL_ECHO=false

# 启动 Celery Beat 并过滤日志
celery -A src.talent_platform.scheduler.celery_app beat \
    --loglevel=warning \
    --pidfile=celerybeat.pid 2>&1 | \
    grep -v "DEBUG\|received task\|task.*succeeded\|Remember to restart celerybeat"

echo "✅ Celery Beat 已启动（清洁模式）" 