#!/usr/bin/env python3
"""
任务更新检测诊断测试
深度分析为什么任务更新不能被检测到
"""

import os
import sys
import time
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.scheduler.database_scheduler import DatabaseScheduler
from talent_platform.logger import logger


def create_test_task():
    """创建测试任务"""
    task_data = {
        "id": "update_detection_test",
        "name": "更新检测测试任务",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "original_test"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 300},  # 5分钟
        "enabled": True,
        "description": "用于测试更新检测的任务",
        "priority": 5
    }
    
    with get_scheduler_db_session() as session:
        # 清理可能存在的任务
        existing = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == task_data["id"]
        ).first()
        if existing:
            session.delete(existing)
            session.commit()
        
        # 创建新任务
        task = ScheduledTaskModel(**task_data)
        session.add(task)
        session.commit()
        print(f"✅ 创建测试任务: {task_data['id']}")
        return task


def cleanup_test_task():
    """清理测试任务"""
    with get_scheduler_db_session() as session:
        task = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.id == "update_detection_test"
        ).first()
        if task:
            session.delete(task)
            session.commit()
            print("🧹 清理测试任务完成")


def diagnose_timestamp_detection():
    """诊断时间戳检测问题"""
    
    print("🔍 诊断时间戳检测机制...")
    
    with get_scheduler_db_session() as session:
        from sqlalchemy import func
        
        # 检查所有任务的时间戳
        all_tasks = session.query(ScheduledTaskModel).all()
        print(f"\n📊 数据库中共有 {len(all_tasks)} 个任务:")
        
        for task in all_tasks:
            print(f"   {task.id}: created={task.created_at}, updated={task.updated_at}")
        
        # 检查最大时间戳
        max_timestamp = session.query(func.max(ScheduledTaskModel.updated_at)).scalar()
        print(f"\n⏰ 数据库最大 updated_at: {max_timestamp}")
        
        # 检查启用任务
        enabled_tasks = session.query(ScheduledTaskModel).filter(
            ScheduledTaskModel.enabled == True
        ).all()
        print(f"\n✅ 启用任务 ({len(enabled_tasks)} 个):")
        for task in enabled_tasks:
            print(f"   {task.id}: updated={task.updated_at}")


def test_update_detection_issue():
    """测试更新检测问题"""
    
    print("🚨 任务更新检测问题诊断")
    print("=" * 50)
    
    # 创建模拟 Celery app
    class MockApp:
        class conf:
            @staticmethod
            def get(key, default=None):
                return {"beat_max_loop_interval": 2.0}.get(key, default)
    
    try:
        # 1. 创建测试环境
        print("\n📋 1. 创建测试环境...")
        cleanup_test_task()
        test_task = create_test_task()
        
        # 2. 初始化调度器并建立基线
        print("\n🚀 2. 初始化调度器...")
        scheduler = DatabaseScheduler(app=MockApp())
        
        # 建立基线
        schedule = scheduler.schedule
        print(f"   初始调度表任务数: {len(schedule)}")
        
        # 记录初始状态
        print(f"   调度器状态:")
        print(f"     _last_task_count: {scheduler._last_task_count}")
        print(f"     _last_task_signature: {scheduler._last_task_signature}")
        print(f"     _last_timestamp: {scheduler._last_timestamp}")
        
        # 3. 检查当前时间戳状态
        print("\n⏰ 3. 检查时间戳状态...")
        diagnose_timestamp_detection()
        
        # 4. 🚨 关键测试：更新任务参数
        print("\n📝 4. 🚨 关键测试：更新任务参数...")
        
        with get_scheduler_db_session() as session:
            task = session.get(ScheduledTaskModel, "update_detection_test")
            if task:
                print(f"   更新前:")
                print(f"     parameters: {task.parameters}")
                print(f"     schedule_config: {task.schedule_config}")
                print(f"     updated_at: {task.updated_at}")
                
                # 修改任务参数
                old_updated_at = task.updated_at
                task.parameters = {"operation": "modified_test", "new_param": "test_value"}
                task.schedule_config = {"interval": 180}  # 改为3分钟
                task.description = "已修改的测试任务"
                task.updated_at = datetime.now()  # 强制更新时间戳
                
                session.add(task)
                session.commit()
                
                print(f"   ✅ 任务已更新:")
                print(f"     parameters: {task.parameters}")
                print(f"     schedule_config: {task.schedule_config}")
                print(f"     updated_at: {task.updated_at}")
                print(f"     时间戳变化: {old_updated_at} -> {task.updated_at}")
        
        # 5. 检查更新后的时间戳状态
        print("\n🔍 5. 检查更新后的时间戳状态...")
        diagnose_timestamp_detection()
        
        # 6. 测试变化检测
        print("\n🎯 6. 测试变化检测...")
        
        # 等待一下确保时间戳不同
        time.sleep(0.1)
        
        # 手动调用 schedule_changed 查看详细过程
        changed = scheduler.schedule_changed()
        print(f"   schedule_changed() 返回: {changed}")
        
        if changed:
            print("   ✅ 检测到变化")
        else:
            print("   ❌ 未检测到变化")
            
            # 深度诊断为什么没检测到
            print(f"\n🔬 深度诊断:")
            print(f"     当前 _last_timestamp: {scheduler._last_timestamp}")
            
            with get_scheduler_db_session() as session:
                from sqlalchemy import func
                current_timestamp = session.query(func.max(ScheduledTaskModel.updated_at)).scalar()
                print(f"     数据库 max(updated_at): {current_timestamp}")
                print(f"     时间戳比较: {current_timestamp} vs {scheduler._last_timestamp}")
                print(f"     时间戳相等: {current_timestamp == scheduler._last_timestamp}")
                
                if current_timestamp and scheduler._last_timestamp:
                    diff = (current_timestamp - scheduler._last_timestamp).total_seconds()
                    print(f"     时间戳差异: {diff} 秒")
        
        # 7. 测试调度表重新加载
        print("\n📊 7. 测试调度表重新加载...")
        
        if changed:
            new_schedule = scheduler.schedule
            print(f"   重新加载后任务数: {len(new_schedule)}")
            
            if "update_detection_test" in new_schedule:
                entry = new_schedule["update_detection_test"]
                print(f"   任务调度配置:")
                print(f"     schedule: {entry.schedule}")
                print(f"     task: {entry.task}")
                
                # 检查参数是否更新
                if hasattr(entry, 'model') and entry.model:
                    print(f"     model.parameters: {entry.model.parameters}")
                    print(f"     model.schedule_config: {entry.model.schedule_config}")
                    
                    if "modified_test" in str(entry.model.parameters):
                        print("   ✅ 任务参数已更新")
                    else:
                        print("   ❌ 任务参数未更新")
        else:
            print("   ❌ 调度表未重新加载")
        
        print("\n" + "=" * 50)
        print("🎯 诊断总结:")
        
        if changed:
            print("   ✅ 变化检测机制工作正常")
        else:
            print("   ❌ 变化检测机制存在问题")
            print("   可能的原因:")
            print("     1. 时间戳更新不正确")
            print("     2. 时间戳精度问题")
            print("     3. 检测逻辑有缺陷")
            print("     4. 缓存或同步问题")
        
        return changed
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        logger.error(f"Update detection diagnosis failed: {e}", exc_info=True)
        return False
        
    finally:
        print("\n🧹 清理测试环境...")
        cleanup_test_task()


if __name__ == "__main__":
    try:
        print("🚀 开始任务更新检测问题诊断...")
        
        result = test_update_detection_issue()
        
        if result:
            print("\n✅ 变化检测工作正常")
        else:
            print("\n⚠️  发现变化检测问题，需要修复")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  诊断中断")
        cleanup_test_task()
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}", exc_info=True)
        print(f"\n❌ 诊断异常: {e}")
        cleanup_test_task() 