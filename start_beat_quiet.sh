#!/bin/bash
# 
# 静默启动 Celery Beat（无 SQL 日志）
# 用于生产环境或日常开发
#

echo "🚀 启动 Celery Beat (DatabaseScheduler) - 静默模式"
echo "======================================================"

# 确保 SQL 日志关闭
export SQL_ECHO=false

# 启动 Celery Beat
echo "📅 使用 DatabaseScheduler 启动调度器..."
echo "📊 日志级别: INFO"
echo "🔇 SQL 日志: 已关闭"
echo ""

celery -A src.talent_platform.scheduler.celery_app beat \
    --loglevel=info \
    --pidfile=celerybeat.pid \
    --schedule=/tmp/celerybeat-schedule

echo "🎉 Celery Beat 启动完成！"
echo ""
echo "📚 相关命令:"
echo "   查看日志: tail -f logs/*"
echo "   停止服务: pkill -f 'celery.*beat'"
echo "   开启 SQL 日志: SQL_ECHO=true ./start_beat_quiet.sh" 