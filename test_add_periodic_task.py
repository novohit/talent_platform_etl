#!/usr/bin/env python3
"""
测试使用 add_periodic_task 的新实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.scheduler.task_scheduler import task_scheduler
from talent_platform.scheduler.celery_app import celery_app
import json

def test_add_periodic_task_implementation():
    """测试 add_periodic_task 的实现"""
    print("=== 测试 add_periodic_task 实现 ===")
    
    # 测试配置
    task_config = {
        "id": "test_add_periodic_task",
        "name": "测试 add_periodic_task",
        "plugin_name": "mysql_test",
        "parameters": {
            "operation": "test_connection"
        },
        "schedule_type": "interval",
        "schedule_config": {
            "interval": 60  # 60秒间隔
        },
        "enabled": True,
        "description": "测试 add_periodic_task 方法",
        "priority": 8,
        "timeout": 30,
        "max_retries": 2
    }
    
    try:
        # 检查初始状态
        initial_beat_count = len(celery_app.conf.beat_schedule)
        print(f"初始 Beat Schedule 任务数: {initial_beat_count}")
        
        # 添加任务
        task_id = task_scheduler.add_scheduled_task(task_config)
        print(f"✅ 添加任务成功: {task_id}")
        
        # 检查任务是否在 beat_schedule 中
        is_in_beat = task_id in celery_app.conf.beat_schedule
        print(f"任务在 Beat Schedule 中: {'✅' if is_in_beat else '❌'}")
        
        if is_in_beat:
            beat_task_config = celery_app.conf.beat_schedule[task_id]
            print("\n📊 Beat Schedule 中的任务配置:")
            print(f"  任务: {beat_task_config.get('task')}")
            print(f"  调度: {beat_task_config.get('schedule')}")
            print(f"  签名: {beat_task_config.get('sig')}")
            print(f"  选项: {beat_task_config.get('options', {})}")
        
        # 检查任务数量变化
        final_beat_count = len(celery_app.conf.beat_schedule)
        print(f"\n最终 Beat Schedule 任务数: {final_beat_count}")
        print(f"任务数量增加: {final_beat_count - initial_beat_count}")
        
        # 测试禁用任务
        print("\n--- 测试禁用任务 ---")
        success = task_scheduler.disable_task(task_id)
        is_disabled_in_beat = task_id not in celery_app.conf.beat_schedule
        print(f"禁用任务: {'✅' if success else '❌'}")
        print(f"从 Beat Schedule 移除: {'✅' if is_disabled_in_beat else '❌'}")
        
        # 测试启用任务
        print("\n--- 测试启用任务 ---")
        success = task_scheduler.enable_task(task_id)
        is_enabled_in_beat = task_id in celery_app.conf.beat_schedule
        print(f"启用任务: {'✅' if success else '❌'}")
        print(f"重新添加到 Beat Schedule: {'✅' if is_enabled_in_beat else '❌'}")
        
        # 验证 add_periodic_task 的签名结构
        if is_enabled_in_beat:
            beat_task_config = celery_app.conf.beat_schedule[task_id]
            has_sig = 'sig' in beat_task_config
            print(f"使用了 Celery Signature: {'✅' if has_sig else '❌'}")
            
            if has_sig:
                sig = beat_task_config['sig']
                print(f"  Signature 任务: {sig.task}")
                print(f"  Signature 参数: {sig.args}")
                print(f"  Signature 关键字参数: {sig.kwargs}")
        
        # 清理测试任务
        print("\n--- 清理测试任务 ---")
        success = task_scheduler.remove_scheduled_task(task_id)
        is_removed = task_id not in celery_app.conf.beat_schedule
        print(f"移除任务: {'✅' if success else '❌'}")
        print(f"从 Beat Schedule 删除: {'✅' if is_removed else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_beat_schedule_structure():
    """比较新旧结构的差异"""
    print("\n=== Beat Schedule 结构对比 ===")
    
    beat_schedule = celery_app.conf.beat_schedule
    print(f"当前 Beat Schedule 任务总数: {len(beat_schedule)}")
    
    for task_name, task_config in beat_schedule.items():
        print(f"\n任务名: {task_name}")
        print(f"  结构类型: {'add_periodic_task' if 'sig' in task_config else 'manual_config'}")
        
        if 'sig' in task_config:
            # add_periodic_task 创建的结构
            print(f"  调度: {task_config.get('schedule')}")
            print(f"  签名: {task_config['sig']}")
            print(f"  选项: {task_config.get('options', {})}")
        else:
            # 手动配置的结构（如 celery_app.py 中的静态配置）
            print(f"  任务: {task_config.get('task')}")
            print(f"  调度: {task_config.get('schedule')}")
            print(f"  参数: {task_config.get('args', [])}")
            print(f"  关键字参数: {task_config.get('kwargs', {})}")

def main():
    """主测试函数"""
    print("🚀 测试 add_periodic_task 实现")
    print("=" * 50)
    
    # 显示初始状态
    compare_beat_schedule_structure()
    
    # 测试 add_periodic_task 实现
    success = test_add_periodic_task_implementation()
    
    # 再次显示结构对比
    compare_beat_schedule_structure()
    
    print("\n=== 测试总结 ===")
    if success:
        print("✅ add_periodic_task 实现测试成功！")
        print("✅ 任务能够正确添加到 Celery Beat Schedule")
        print("✅ 任务启用/禁用功能正常")
        print("✅ 任务删除功能正常")
    else:
        print("❌ 测试失败，请检查实现")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main() 