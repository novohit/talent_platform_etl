#!/bin/bash
# 🔥 激进重置机制快速测试脚本

echo "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥"
echo "🔥 DatabaseScheduler v3 激进重置机制快速测试"
echo "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥"

# 检查依赖
echo "🔍 检查环境依赖..."

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    exit 1
fi

# 检查数据库连接
echo "🔗 检查数据库连接..."
if ! python -c "from src.talent_platform.db.database import get_scheduler_db_session; print('✅ 数据库连接正常')" 2>/dev/null; then
    echo "❌ 数据库连接失败"
    echo "💡 请先运行: python create_tables.py"
    exit 1
fi

# 检查是否有其他 Beat 进程
echo "🔍 检查现有 Beat 进程..."
if pgrep -f "celery.*beat" > /dev/null; then
    echo "⚠️  检测到现有 Celery Beat 进程"
    echo "📋 现有进程："
    pgrep -af "celery.*beat"
    echo ""
    read -p "是否要停止现有进程并继续测试? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 停止现有 Beat 进程..."
        pkill -f "celery.*beat"
        sleep 2
    else
        echo "❌ 测试取消"
        exit 1
    fi
fi

# 清理旧的测试数据
echo "🧹 清理旧的测试数据..."
python -c "
import sys
sys.path.insert(0, 'src')
from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel

try:
    with get_scheduler_db_session() as session:
        old_tasks = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id.like('aggressive_test_%')
        ).all()
        for task in old_tasks:
            session.delete(task)
        session.commit()
        print(f'✅ 清理了 {len(old_tasks)} 个旧测试任务')
except Exception as e:
    print(f'⚠️ 清理失败: {e}')
"

echo ""
echo "🚀 启动激进重置测试..."
echo "⏳ 测试将运行约 3-5 分钟"
echo "📜 观察日志输出，寻找 🔥 激进重置相关消息"
echo ""

# 运行测试
python test_aggressive_reset.py

# 获取退出状态
test_result=$?

echo ""
echo "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥"

if [ $test_result -eq 0 ]; then
    echo "🎉 激进重置机制测试成功！"
    echo "✅ enabled 0→1 问题已解决"
    echo "✅ 参数更新问题已解决"
    echo "✅ 配置修改问题已解决"
    echo ""
    echo "💡 现在你可以安全地使用数据库管理定时任务："
    echo "   - 启用/禁用任务会在 5 秒内生效"
    echo "   - 参数/配置修改会在 10 秒内生效"
    echo "   - 无需重启 Beat 进程"
else
    echo "💥 激进重置机制测试失败！"
    echo "🔧 可能的问题："
    echo "   - 数据库连接问题"
    echo "   - Redis/RabbitMQ 连接问题"
    echo "   - 端口占用问题"
    echo ""
    echo "🛠️ 调试建议："
    echo "   1. 检查数据库状态: python create_tables.py"
    echo "   2. 检查 Redis: redis-cli ping"
    echo "   3. 查看详细日志: python test_aggressive_reset.py 2>&1 | tee test.log"
fi

echo "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥"

exit $test_result 