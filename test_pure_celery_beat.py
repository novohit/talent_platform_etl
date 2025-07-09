#!/usr/bin/env python3
"""
测试纯 Celery Beat + 持久化定时任务功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.scheduler.task_scheduler import task_scheduler
from talent_platform.scheduler.celery_app import celery_app
import json
import time

def test_add_dynamic_task():
    """测试添加动态定时任务"""
    print("=== 测试添加动态定时任务 ===")
    
    # 测试配置 - 每30秒执行一次MySQL测试
    task_config = {
        "id": "test_mysql_interval",
        "name": "MySQL间隔测试",
        "plugin_name": "mysql_test",
        "parameters": {
            "operation": "test_connection"
        },
        "schedule_type": "interval",
        "schedule_config": {
            "interval": 30  # 30秒间隔
        },
        "enabled": True,
        "description": "用于测试的MySQL连接检查任务",
        "priority": 7
    }
    
    try:
        task_id = task_scheduler.add_scheduled_task(task_config)
        print(f"✅ 成功添加动态任务: {task_id}")
        return task_id
    except Exception as e:
        print(f"❌ 添加动态任务失败: {e}")
        return None

def test_add_cron_task():
    """测试添加 Cron 表达式任务"""
    print("\n=== 测试添加 Cron 定时任务 ===")
    
    # 测试配置 - 每2分钟执行一次
    task_config = {
        "id": "test_mysql_cron",
        "name": "MySQL Cron测试",
        "plugin_name": "mysql_test", 
        "parameters": {
            "operation": "health_check"
        },
        "schedule_type": "cron",
        "schedule_config": {
            "cron": "*/2 * * * *"  # 每2分钟执行
        },
        "enabled": True,
        "description": "Cron调度的MySQL健康检查",
        "timeout": 60
    }
    
    try:
        task_id = task_scheduler.add_scheduled_task(task_config)
        print(f"✅ 成功添加 Cron 任务: {task_id}")
        return task_id
    except Exception as e:
        print(f"❌ 添加 Cron 任务失败: {e}")
        return None

def test_list_tasks():
    """测试列出所有任务"""
    print("\n=== 当前调度任务列表 ===")
    
    tasks = task_scheduler.get_scheduled_tasks()
    print(f"总任务数: {len(tasks)}")
    
    for task in tasks:
        print(f"任务ID: {task['id']}")
        print(f"名称: {task['name']}")
        print(f"插件: {task['plugin_name']}")
        print(f"类型: {task['schedule_type']}")
        print(f"配置: {task['schedule_config']}")
        print(f"启用: {task['enabled']}")
        print(f"描述: {task.get('description', 'N/A')}")
        print(f"最后执行: {task['last_run']}")
        print("-" * 50)

def test_celery_beat_status():
    """测试 Celery Beat 调度状态"""
    print("\n=== Celery Beat 调度状态 ===")
    
    beat_schedule = celery_app.conf.beat_schedule
    print(f"Beat Schedule 中的任务数: {len(beat_schedule)}")
    
    for task_name, task_config in beat_schedule.items():
        print(f"任务名: {task_name}")
        print(f"调度: {task_config.get('schedule')}")
        print(f"任务: {task_config.get('task')}")
        print(f"参数: {task_config.get('args', [])} {task_config.get('kwargs', {})}")
        print(f"选项: {task_config.get('options', {})}")
        print("-" * 40)

def test_persistence():
    """测试数据库持久化"""
    print("\n=== 测试数据库持久化 ===")
    
    # 添加一个测试任务
    test_task_config = {
        "id": "persistence_test",
        "name": "持久化测试任务",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "stats"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 120},
        "enabled": True,
        "description": "用于测试数据库持久化的任务"
    }
    
    print("1. 添加测试任务...")
    task_id = task_scheduler.add_scheduled_task(test_task_config)
    print(f"   任务ID: {task_id}")
    
    # 检查是否在 Celery Beat 中
    is_in_beat = task_id in celery_app.conf.beat_schedule
    print(f"2. 任务是否在 Celery Beat 中: {'✅' if is_in_beat else '❌'}")
    
    # 模拟重启 - 重新加载任务
    print("3. 模拟重启 - 清除内存并重新加载...")
    original_count = len(task_scheduler.scheduled_tasks)
    task_scheduler.scheduled_tasks.clear()
    
    # 清除 Celery Beat 调度（模拟重启）
    original_beat_tasks = list(celery_app.conf.beat_schedule.keys())
    for task_name in original_beat_tasks:
        if task_name.startswith('test_') or task_name == 'persistence_test':
            del celery_app.conf.beat_schedule[task_name]
    
    # 重新加载
    loaded_count = task_scheduler.load_persisted_tasks()
    print(f"4. 重新加载的任务数: {loaded_count}")
    
    # 检查任务是否恢复
    is_restored = task_id in task_scheduler.scheduled_tasks
    is_in_beat_again = task_id in celery_app.conf.beat_schedule
    print(f"5. 任务是否恢复到内存: {'✅' if is_restored else '❌'}")
    print(f"6. 任务是否恢复到 Celery Beat: {'✅' if is_in_beat_again else '❌'}")
    
    # 清理测试任务
    print("7. 清理测试任务...")
    task_scheduler.remove_scheduled_task(task_id)
    print("   清理完成")

def test_task_operations():
    """测试任务操作"""
    print("\n=== 测试任务操作 ===")
    
    # 添加一个测试任务
    task_config = {
        "id": "test_operations",
        "name": "操作测试任务",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "stats"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 60},
        "enabled": True
    }
    
    task_id = task_scheduler.add_scheduled_task(task_config)
    print(f"✅ 添加测试任务: {task_id}")
    
    # 检查是否在 Celery Beat 中
    is_in_beat = task_id in celery_app.conf.beat_schedule
    print(f"任务在 Celery Beat 中: {'✅' if is_in_beat else '❌'}")
    
    # 测试禁用任务
    success = task_scheduler.disable_task(task_id)
    is_disabled_in_beat = task_id not in celery_app.conf.beat_schedule
    print(f"禁用任务: {'✅' if success else '❌'}")
    print(f"从 Celery Beat 移除: {'✅' if is_disabled_in_beat else '❌'}")
    
    # 测试启用任务
    success = task_scheduler.enable_task(task_id)
    is_enabled_in_beat = task_id in celery_app.conf.beat_schedule
    print(f"启用任务: {'✅' if success else '❌'}")
    print(f"重新添加到 Celery Beat: {'✅' if is_enabled_in_beat else '❌'}")
    
    # 测试移除任务
    success = task_scheduler.remove_scheduled_task(task_id)
    is_removed_from_beat = task_id not in celery_app.conf.beat_schedule
    print(f"移除任务: {'✅' if success else '❌'}")
    print(f"从 Celery Beat 删除: {'✅' if is_removed_from_beat else '❌'}")

def test_architecture_validation():
    """验证架构的正确性"""
    print("\n=== 架构验证 ===")
    
    # 检查是否没有检查器任务
    has_checker = 'dynamic_task_checker' in celery_app.conf.beat_schedule
    print(f"1. 无混乱检查器: {'✅' if not has_checker else '❌'}")
    
    # 检查所有任务都是真正的 Celery Beat 任务
    memory_tasks = set(task_scheduler.scheduled_tasks.keys())
    beat_tasks = set(celery_app.conf.beat_schedule.keys())
    
    # 过滤掉系统任务
    system_tasks = {'monitor-db-changes', 'mysql-health-check', 'mysql-daily-test'}
    memory_user_tasks = memory_tasks - system_tasks
    beat_user_tasks = beat_tasks - system_tasks
    
    tasks_match = memory_user_tasks.issubset(beat_user_tasks)
    print(f"2. 内存任务都在 Celery Beat 中: {'✅' if tasks_match else '❌'}")
    print(f"   内存中用户任务: {memory_user_tasks}")
    print(f"   Beat中用户任务: {beat_user_tasks}")
    
    # 检查启用的任务都在 Beat 中
    enabled_tasks = {task_id for task_id, task in task_scheduler.scheduled_tasks.items() if task.enabled}
    enabled_in_beat = enabled_tasks.issubset(beat_tasks)
    print(f"3. 启用任务都在 Beat 中: {'✅' if enabled_in_beat else '❌'}")

def main():
    """主测试函数"""
    print("🚀 开始测试纯 Celery Beat + 持久化定时任务功能")
    print("=" * 60)
    
    # 先验证架构
    test_architecture_validation()
    
    # 测试添加不同类型的任务
    interval_task_id = test_add_dynamic_task()
    cron_task_id = test_add_cron_task()
    
    # 列出所有任务
    test_list_tasks()
    
    # 显示 Celery Beat 状态
    test_celery_beat_status()
    
    # 测试持久化功能
    test_persistence()
    
    # 测试任务操作
    test_task_operations()
    
    # 最终架构验证
    print("\n=== 最终架构验证 ===")
    test_architecture_validation()
    
    print("\n=== 测试摘要 ===")
    print(f"间隔任务添加: {'✅' if interval_task_id else '❌'}")
    print(f"Cron任务添加: {'✅' if cron_task_id else '❌'}")
    
    # 显示系统状态
    health = task_scheduler.health_check()
    print(f"\n系统健康检查:")
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main() 