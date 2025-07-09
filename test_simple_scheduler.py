#!/usr/bin/env python3
"""
简洁数据库调度器测试
验证新的简洁方案能否正确工作
"""

import os
import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.scheduler.simple_database_scheduler import SimpleDatabaseScheduler
from talent_platform.logger import logger


def create_test_task():
    """创建一个简单的测试任务"""
    task_data = {
        "id": "simple_test_task",
        "name": "简洁调度器测试任务",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "simple_test"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 60},  # 每分钟
        "enabled": True,
        "description": "测试简洁数据库调度器",
        "priority": 5
    }
    
    with get_scheduler_db_session() as session:
        # 清理现有任务
        existing = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == task_data["id"]
        ).first()
        if existing:
            session.delete(existing)
        
        # 创建新任务
        task = ScheduledTaskModel(**task_data)
        session.add(task)
        session.commit()
        
        print(f"✅ 创建测试任务: {task_data['id']}")
        return task


def test_scheduler_basic_functionality():
    """测试调度器基本功能"""
    print("\n🔍 测试调度器基本功能...")
    
    # 创建测试任务
    task = create_test_task()
    
    # 创建调度器实例（模拟）
    scheduler = SimpleDatabaseScheduler()
    
    # 测试调度表加载
    schedule = scheduler.all_as_schedule()
    print(f"   📋 加载调度表: {len(schedule)} 个任务")
    
    if task.id in schedule:
        print(f"   ✅ 任务 {task.id} 成功加载到调度表")
        entry = schedule[task.id]
        print(f"   📊 任务信息: {entry.name}, 调度: {entry.schedule}")
    else:
        print(f"   ❌ 任务 {task.id} 未在调度表中找到")
    
    return schedule


def test_change_detection():
    """测试变更检测机制"""
    print("\n🔍 测试变更检测机制...")
    
    scheduler = SimpleDatabaseScheduler()
    
    # 初始哈希
    initial_hash = scheduler._calculate_tasks_hash()
    print(f"   📝 初始任务哈希: {initial_hash[:8]}...")
    
    # 等待一秒
    time.sleep(1)
    
    # 修改任务参数
    with get_scheduler_db_session() as session:
        task = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == "simple_test_task"
        ).first()
        
        if task:
            # 修改参数
            task.parameters = {"operation": "modified_test", "new_param": "test_value"}
            task.updated_at = datetime.now()
            session.add(task)
            session.commit()
            print("   📝 已修改任务参数")
        
    # 计算新哈希
    new_hash = scheduler._calculate_tasks_hash()
    print(f"   📝 修改后哈希: {new_hash[:8]}...")
    
    # 检查变更检测
    if initial_hash != new_hash:
        print("   ✅ 变更检测成功：哈希值不同")
        return True
    else:
        print("   ❌ 变更检测失败：哈希值相同")
        return False


def test_enable_disable():
    """测试启用/禁用功能"""
    print("\n🔍 测试启用/禁用功能...")
    
    scheduler = SimpleDatabaseScheduler()
    
    # 获取启用状态的调度表
    enabled_schedule = scheduler.all_as_schedule()
    enabled_count = len(enabled_schedule)
    print(f"   📊 启用状态: {enabled_count} 个任务")
    
    # 禁用任务
    with get_scheduler_db_session() as session:
        task = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == "simple_test_task"
        ).first()
        
        if task:
            task.enabled = False
            task.updated_at = datetime.now()
            session.add(task)
            session.commit()
            print("   🚫 已禁用测试任务")
    
    # 获取禁用后的调度表
    disabled_schedule = scheduler.all_as_schedule()
    disabled_count = len(disabled_schedule)
    print(f"   📊 禁用后: {disabled_count} 个任务")
    
    # 重新启用任务
    with get_scheduler_db_session() as session:
        task = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == "simple_test_task"
        ).first()
        
        if task:
            task.enabled = True
            task.updated_at = datetime.now()
            session.add(task)
            session.commit()
            print("   ✅ 已重新启用测试任务")
    
    # 获取重新启用后的调度表
    reenabled_schedule = scheduler.all_as_schedule()
    reenabled_count = len(reenabled_schedule)
    print(f"   📊 重新启用后: {reenabled_count} 个任务")
    
    # 验证结果
    if disabled_count < enabled_count:
        print("   ✅ 禁用功能正常")
    else:
        print("   ❌ 禁用功能异常")
    
    if reenabled_count == enabled_count:
        print("   ✅ 重新启用功能正常")
        return True
    else:
        print("   ❌ 重新启用功能异常")
        return False


def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    with get_scheduler_db_session() as session:
        # 删除测试任务
        session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == "simple_test_task"
        ).delete()
        session.commit()
        print("   ✅ 清理完成")


def main():
    """主测试流程"""
    print("🚀 开始测试简洁数据库调度器")
    print("=" * 50)
    
    try:
        # 测试基本功能
        schedule = test_scheduler_basic_functionality()
        
        if not schedule:
            print("❌ 基本功能测试失败，停止测试")
            return
        
        # 测试变更检测
        change_detection_ok = test_change_detection()
        
        # 测试启用/禁用
        enable_disable_ok = change_detection_ok and test_enable_disable()
        
        # 总结
        print("\n" + "=" * 50)
        print("📊 测试结果总结:")
        print(f"   基本功能: {'✅ 通过' if schedule else '❌ 失败'}")
        print(f"   变更检测: {'✅ 通过' if change_detection_ok else '❌ 失败'}")
        print(f"   启用/禁用: {'✅ 通过' if enable_disable_ok else '❌ 失败'}")
        
        if schedule and change_detection_ok and enable_disable_ok:
            print("\n🎉 所有测试通过！简洁数据库调度器工作正常")
        else:
            print("\n⚠️  部分测试失败，请检查实现")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据
        cleanup_test_data()


if __name__ == "__main__":
    main() 