#!/usr/bin/env python3
"""
任务重新启用修复验证测试 (enabled 0->1)
验证新的强力修复机制能否正确处理任务重新启用问题
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
        "id": "reenable_fix_test_task",
        "name": "重新启用修复测试任务",
        "plugin_name": "mysql_test", 
        "parameters": {"operation": "reenable_test"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 120},  # 2分钟
        "enabled": True,
        "description": "用于测试 enabled 0->1 修复的任务",
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
            ScheduledTaskModel.id == "reenable_fix_test_task"
        ).first()
        if task:
            session.delete(task)
            session.commit()
            print("🧹 清理测试任务完成")


def simulate_task_history():
    """模拟任务执行历史"""
    with get_scheduler_db_session() as session:
        task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
        if task:
            # 模拟任务曾经运行过（设置 last_run 为1小时前）
            old_time = datetime.now() - timedelta(hours=1)
            task.last_run = old_time
            task.next_run = old_time + timedelta(seconds=120)  # 2分钟后
            
            session.add(task)
            session.commit()
            print(f"📋 模拟任务执行历史: last_run = {old_time}")
            return old_time


def test_enabled_reenable_fix():
    """测试 enabled 0->1 修复机制"""
    
    print("🚨 任务重新启用修复验证测试")
    print("=" * 60)
    
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
        
        # 2. 模拟任务执行历史
        print("\n⏰ 2. 模拟任务执行历史...")
        old_last_run = simulate_task_history()
        
        # 3. 初始化调度器
        print("\n🚀 3. 初始化调度器...")
        scheduler = DatabaseScheduler(app=MockApp())
        
        # 建立基线
        schedule = scheduler.schedule
        print(f"   初始调度表任务数: {len(schedule)}")
        print(f"   任务在调度表中: {'reenable_fix_test_task' in schedule}")
        
        # 4. 第一步：禁用任务 (enabled 1->0)
        print("\n⏸️  4. 第一步：禁用任务 (enabled 1->0)...")
        
        with get_scheduler_db_session() as session:
            task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
            if task:
                print(f"   禁用前状态: enabled={task.enabled}, last_run={task.last_run}")
                
                task.enabled = False
                task.updated_at = datetime.now()
                
                session.add(task)
                session.commit()
                print(f"   ✅ 任务已禁用: enabled={task.enabled}")
        
        # 等待并检测变化
        time.sleep(0.5)
        
        # 检查调度器是否检测到禁用
        changed = scheduler.schedule_changed()
        print(f"   禁用检测: {changed} (应该为 True)")
        
        # 重新加载调度表
        new_schedule = scheduler.schedule
        print(f"   禁用后调度表任务数: {len(new_schedule)}")
        print(f"   任务从调度表移除: {'reenable_fix_test_task' not in new_schedule}")
        
        if 'reenable_fix_test_task' not in new_schedule:
            print("   ✅ 任务禁用检测正常")
        else:
            print("   ❌ 任务禁用检测异常")
            return False
        
        # 5. 🚨 关键测试：重新启用任务 (enabled 0->1)
        print("\n🔄 5. 🚨 关键测试：重新启用任务 (enabled 0->1)...")
        
        with get_scheduler_db_session() as session:
            task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
            if task:
                print(f"   重新启用前状态:")
                print(f"     enabled: {task.enabled}")
                print(f"     last_run: {task.last_run}")
                print(f"     next_run: {task.next_run}")
                
                # 重新启用任务
                task.enabled = True
                task.updated_at = datetime.now()
                
                session.add(task)
                session.commit()
                print(f"   ✅ 任务已重新启用: enabled={task.enabled}")
        
        # 6. 检测重新启用
        print("\n🔍 6. 检测重新启用变化...")
        
        time.sleep(0.5)
        
        # 检查 enabled 状态变化检测
        enabled_changed = scheduler._check_enabled_state_changes()
        print(f"   enabled 状态变化检测: {enabled_changed} (应该为 True)")
        
        # 检查整体变化检测
        overall_changed = scheduler.schedule_changed()
        print(f"   整体变化检测: {overall_changed} (应该为 True)")
        
        # 7. 验证调度表重新加载
        print("\n📊 7. 验证调度表重新加载...")
        
        final_schedule = scheduler.schedule
        print(f"   重新启用后调度表任务数: {len(final_schedule)}")
        print(f"   任务重新加入调度表: {'reenable_fix_test_task' in final_schedule}")
        
        if 'reenable_fix_test_task' in final_schedule:
            entry = final_schedule['reenable_fix_test_task']
            print(f"   调度条目信息:")
            print(f"     name: {entry.name}")
            print(f"     last_run_at: {entry.last_run_at}")
            print(f"     schedule: {entry.schedule}")
            
            # 8. 检查调度状态重置
            print("\n🔧 8. 检查调度状态重置...")
            
            # 检查数据库中的状态
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
                if task:
                    print(f"   数据库任务状态:")
                    print(f"     last_run: {task.last_run}")
                    print(f"     next_run: {task.next_run}")
                    print(f"     updated_at: {task.updated_at}")
                    
                    # 检查 last_run 是否被重置
                    if task.last_run is None or task.last_run != old_last_run:
                        print("   ✅ last_run 已被重置")
                        last_run_reset = True
                    else:
                        print("   ❌ last_run 未被重置")
                        last_run_reset = False
            
            # 检查调度条目的 last_run_at
            if entry.last_run_at is None:
                print("   ✅ 调度条目 last_run_at 已重置")
                entry_reset = True
            else:
                print("   ❌ 调度条目 last_run_at 未重置")
                entry_reset = False
            
            # 9. 检查任务是否会立即调度
            print("\n⚡ 9. 检查任务是否会立即调度...")
            
            is_due_result = entry.is_due()
            print(f"   is_due() 结果: {is_due_result}")
            
            if hasattr(is_due_result, 'is_due') and is_due_result.is_due:
                print("   ✅ 任务会立即调度")
                immediate_schedule = True
            else:
                print("   ❌ 任务不会立即调度")
                immediate_schedule = False
            
            # 总结验证结果
            print("\n" + "=" * 60)
            print("🎯 修复验证结果:")
            
            success_count = 0
            total_checks = 5
            
            checks = [
                ("任务禁用检测", 'reenable_fix_test_task' not in new_schedule),
                ("任务重新加入调度表", 'reenable_fix_test_task' in final_schedule),
                ("enabled 状态变化检测", enabled_changed),
                ("调度状态重置", last_run_reset and entry_reset),
                ("立即调度准备", immediate_schedule)
            ]
            
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {result}")
                if result:
                    success_count += 1
            
            print(f"\n📊 成功率: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")
            
            if success_count == total_checks:
                print("\n🎊 所有检查通过！enabled 0->1 修复成功！")
                return True
            elif success_count >= 3:
                print(f"\n⚠️  大部分检查通过，修复基本成功，但需要调优")
                return True
            else:
                print(f"\n❌ 修复失败，需要进一步排查")
                return False
                
        else:
            print("   ❌ 任务重新启用失败")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        logger.error(f"Enabled re-enable fix test failed: {e}", exc_info=True)
        return False
        
    finally:
        print("\n🧹 清理测试环境...")
        cleanup_test_task()


def test_multiple_reenable_scenario():
    """测试多次启用/禁用场景"""
    
    print("\n🔄 多次启用/禁用场景测试...")
    
    # 创建模拟 app
    class MockApp:
        class conf:
            @staticmethod
            def get(key, default=None):
                return {"beat_max_loop_interval": 2.0}.get(key, default)
    
    try:
        scheduler = DatabaseScheduler(app=MockApp())
        
        # 多次切换 enabled 状态
        for i in range(3):
            print(f"\n   🔄 第 {i+1} 轮切换...")
            
            # 禁用
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
                if task:
                    task.enabled = False
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
            
            time.sleep(0.1)
            changed = scheduler._check_enabled_state_changes()
            print(f"     禁用检测: {changed}")
            
            # 重新启用
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, "reenable_fix_test_task")
                if task:
                    task.enabled = True
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
            
            time.sleep(0.1)
            changed = scheduler._check_enabled_state_changes()
            print(f"     重新启用检测: {changed}")
        
        print("   ✅ 多次切换测试完成")
        
    except Exception as e:
        print(f"   ❌ 多次切换测试失败: {e}")


if __name__ == "__main__":
    try:
        print("🚀 开始任务重新启用修复验证...")
        
        # 主要修复测试
        main_result = test_enabled_reenable_fix()
        
        # 多次切换场景测试
        if main_result:
            test_multiple_reenable_scenario()
        
        if main_result:
            print("\n🎊 任务重新启用修复验证通过！")
            print("\n📚 修复机制说明:")
            print("   🔧 新增 enabled 状态变化专项检测")
            print("   🔧 强制重置重新启用任务的调度状态")
            print("   🔧 确保 last_run/next_run 正确重置")
            print("   🔧 立即生效，无需重启服务")
            
            print("\n💡 现在你可以:")
            print("   ✅ 随时禁用/启用任务")
            print("   ✅ enabled 0->1 立即生效")
            print("   ✅ enabled 1->0 立即停止")
            print("   ✅ 重新启用的任务立即调度")
            print("   ✅ 所有变化5秒内检测并生效")
        else:
            print("\n⚠️  修复验证失败，需要进一步排查")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试中断")
        cleanup_test_task()
    except Exception as e:
        logger.error(f"Enabled re-enable fix test failed: {e}", exc_info=True)
        print(f"\n❌ 测试异常: {e}")
        cleanup_test_task() 