#!/usr/bin/env python3
"""
测试 DatabaseScheduler 功能
验证数据库调度器是否正确从数据库读取任务并调度
"""

import os
import sys
import time
import uuid
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.scheduler.task_scheduler import task_scheduler
from talent_platform.logger import logger


def test_database_scheduler():
    """测试数据库调度器功能"""
    
    print("🚀 DatabaseScheduler 功能测试")
    print("=" * 60)
    
    # 1. 加载现有任务
    print("\n📋 1. 加载现有任务...")
    loaded_count = task_scheduler.load_persisted_tasks()
    print(f"   ✅ 加载了 {loaded_count} 个任务")
    
    # 2. 创建测试任务
    print("\n➕ 2. 创建测试任务...")
    
    # 创建间隔任务
    interval_task_config = {
        "name": f"DatabaseScheduler间隔测试-{uuid.uuid4().hex[:8]}",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "health_check"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 60},  # 每分钟
        "enabled": True,
        "priority": 5,
        "timeout": 30,
        "max_retries": 3
    }
    
    interval_task_id = task_scheduler.add_scheduled_task(interval_task_config)
    print(f"   ✅ 创建间隔任务: {interval_task_id}")
    
    # 创建 Cron 任务
    cron_task_config = {
        "name": f"DatabaseScheduler定时测试-{uuid.uuid4().hex[:8]}",
        "plugin_name": "mysql_test", 
        "parameters": {"operation": "test_connection"},
        "schedule_type": "cron",
        "schedule_config": {"cron": "*/2 * * * *"},  # 每2分钟
        "enabled": True,
        "priority": 3,
        "timeout": 60,
        "max_retries": 2
    }
    
    cron_task_id = task_scheduler.add_scheduled_task(cron_task_config)
    print(f"   ✅ 创建定时任务: {cron_task_id}")
    
    # 3. 列出所有任务
    print("\n📊 3. 查看所有调度任务...")
    tasks = task_scheduler.get_scheduled_tasks()
    print(f"   📋 总任务数: {len(tasks)}")
    
    for task in tasks[-5:]:  # 显示最后5个任务
        status = "🟢 启用" if task['enabled'] else "🔴 禁用"
        print(f"   {status} {task['name']} ({task['schedule_type']})")
    
    # 4. 测试任务启用/禁用
    print("\n🔄 4. 测试任务启用/禁用...")
    
    # 禁用任务
    success = task_scheduler.disable_task(interval_task_id)
    print(f"   {'✅' if success else '❌'} 禁用任务: {interval_task_id}")
    
    # 重新启用任务
    success = task_scheduler.enable_task(interval_task_id)
    print(f"   {'✅' if success else '❌'} 启用任务: {interval_task_id}")
    
    # 5. 验证 DatabaseScheduler 说明
    print("\n🔍 5. DatabaseScheduler 工作原理 (已优化):")
    print("   📖 DatabaseScheduler 采用智能检测机制:")
    print("      • 每5秒检查数据库是否有变化（而非强制同步）")
    print("      • 只有检测到变化时才重新加载任务")
    print("      • 通过 updated_at 字段追踪变化")
    print("      • 显著减少数据库查询次数")
    print("      • 任务启用/禁用会立即被检测到")
    
    print("\n   ⚠️  重要说明:")
    print("      • 不再使用默认的 PersistentScheduler")
    print("      • 不再依赖 celerybeat-schedule 文件")
    print("      • 所有调度数据都来自数据库")
    print("      • 重启后任务不会丢失")
    
    # 6. 显示 Celery Beat 启动提示
    print("\n🚀 6. 启动 Celery Beat 验证:")
    print("   📝 运行以下命令启动 Celery Beat:")
    print("      celery -A src.talent_platform.scheduler.celery_app beat --loglevel=info")
    
    print("\n   📊 在 Beat 日志中你应该看到:")
    print("      • DatabaseScheduler initialized with max_interval=5s")
    print("      • Setting up database schedule...")
    print("      • DatabaseScheduler: initial read")
    print("      • Schedule updated: 0 -> X tasks")
    print("      • 只有在任务变化时才会看到 'Schedule changed, reloading...'")
    print("      • 大部分时间不会有数据库查询日志（高效！）")
    
    # 7. 测试手动触发
    print("\n⚡ 7. 测试手动触发...")
    
    try:
        # 手动触发 mysql_test 插件
        trigger_result = task_scheduler.trigger_plugin(
            "mysql_test", 
            {"operation": "health_check"}
        )
        print(f"   ✅ 手动触发成功，任务ID: {trigger_result}")
        
        # 检查任务状态
        time.sleep(1)
        status = task_scheduler.get_task_status(trigger_result)
        print(f"   📊 任务状态: {status['status']}")
        
    except Exception as e:
        print(f"   ⚠️  手动触发失败 (需要 Celery Worker 运行): {e}")
    
    # 8. 清理测试任务（可选）
    print(f"\n🧹 8. 清理测试任务...")
    
    # 询问是否删除测试任务
    try:
        choice = input("   删除创建的测试任务? (y/N): ").strip().lower()
        if choice == 'y':
            task_scheduler.remove_scheduled_task(interval_task_id)
            task_scheduler.remove_scheduled_task(cron_task_id)
            print("   ✅ 测试任务已删除")
        else:
            print("   📋 保留测试任务")
            print(f"      间隔任务ID: {interval_task_id}")
            print(f"      定时任务ID: {cron_task_id}")
    except KeyboardInterrupt:
        print("\n   📋 保留测试任务")
    
    print("\n" + "=" * 60)
    print("🎉 DatabaseScheduler 测试完成!")
    print("\n📚 参考文档:")
    print("   • DATABASE_SCHEDULER_GUIDE.md - 详细使用指南")
    print("   • PURE_CELERY_BEAT_GUIDE.md")
    print("   • SCHEDULER_USAGE.md")
    
    print("\n🧪 额外测试:")
    print("   运行 SQLModel 兼容性测试:")
    print("   python test_sqlmodel_compatibility.py")
    print("")
    print("   🚨 重要：运行调度变化检测测试:")
    print("   python test_schedule_changes.py")
    print("   (验证禁用/删除任务能被正确检测)")
    print("")
    print("   🔄 关键：运行任务重新启用测试:")
    print("   python test_task_reenable.py")
    print("   (验证重新启用的任务能正确调度)")


if __name__ == "__main__":
    try:
        test_database_scheduler()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试中断")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}") 