#!/usr/bin/env python3
"""
🔥 激进重置机制测试脚本

验证 DatabaseScheduler v3 的激进重置机制是否能正确处理：
1. enabled 0->1 转换
2. 参数更新
3. 配置修改
4. 强制堆重建
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.scheduler.task_scheduler import task_scheduler


class AggressiveResetTester:
    """🔥 激进重置测试器"""
    
    def __init__(self):
        self.test_task_id = "aggressive_test_task"
        self.beat_process = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔥 Setting up AGGRESSIVE test environment...")
        
        # 清理现有测试任务
        self.cleanup_test_task()
        
        # 创建测试任务（禁用状态）
        task_config = {
            "id": self.test_task_id,
            "name": "Aggressive Reset Test Task",
            "plugin_name": "mysql_test",
            "parameters": {"operation": "test", "message": "initial"},
            "schedule_type": "interval",
            "schedule_config": {"interval": 30},  # 30秒间隔
            "enabled": False,  # 🔥 初始禁用
            "description": "Test task for aggressive reset mechanism",
            "priority": 9
        }
        
        task_scheduler.add_scheduled_task(task_config)
        print(f"✅ Created test task: {self.test_task_id} (DISABLED)")
        
    def start_beat_process(self):
        """启动 Celery Beat 进程"""
        print("🚀 Starting Celery Beat with aggressive scheduler...")
        
        cmd = [
            "celery", "-A", "src.talent_platform.scheduler.celery_app", 
            "beat", "--loglevel=info"
        ]
        
        try:
            self.beat_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            print("✅ Beat process started")
            time.sleep(3)  # 等待启动
            return True
        except Exception as e:
            print(f"❌ Failed to start beat process: {e}")
            return False
    
    def stop_beat_process(self):
        """停止 Beat 进程"""
        if self.beat_process:
            print("🛑 Stopping Beat process...")
            self.beat_process.terminate()
            self.beat_process.wait()
            self.beat_process = None
    
    def cleanup_test_task(self):
        """清理测试任务"""
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, self.test_task_id)
                if task:
                    session.delete(task)
                    session.commit()
                    print(f"🧹 Cleaned up existing test task: {self.test_task_id}")
        except Exception as e:
            print(f"Failed to cleanup test task: {e}")
    
    def get_task_status(self):
        """获取任务状态"""
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, self.test_task_id)
                if task:
                    return {
                        'enabled': task.enabled,
                        'last_run': task.last_run,
                        'next_run': task.next_run,
                        'updated_at': task.updated_at,
                        'parameters': task.parameters
                    }
        except Exception as e:
            print(f"Failed to get task status: {e}")
        return None
    
    def test_enabled_0_to_1_transition(self):
        """🔥 测试 enabled 0->1 转换"""
        print("\n" + "="*60)
        print("🔥 TEST 1: ENABLED 0->1 TRANSITION")
        print("="*60)
        
        # 确认任务当前是禁用状态
        status = self.get_task_status()
        if not status or status['enabled']:
            print("❌ Test task is not in disabled state")
            return False
        
        print(f"📊 Initial status: enabled={status['enabled']}, last_run={status['last_run']}")
        
        # 🔥 激进测试：启用任务
        print("🔥 ENABLING task (0->1)...")
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, self.test_task_id)
                if task:
                    task.enabled = True
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
                    print("✅ Task enabled in database")
        except Exception as e:
            print(f"❌ Failed to enable task: {e}")
            return False
        
        # 等待检测和重新调度
        print("⏳ Waiting for aggressive detection and rescheduling...")
        for i in range(12):  # 60秒最大等待
            time.sleep(5)
            
            # 检查 Beat 日志输出
            if self.beat_process:
                try:
                    # 非阻塞读取进程输出
                    import select
                    if select.select([self.beat_process.stdout], [], [], 0.1)[0]:
                        output = self.beat_process.stdout.readline()
                        if output:
                            print(f"📜 Beat: {output.strip()}")
                            
                            # 检查是否有激进重置的关键日志
                            if any(keyword in output for keyword in [
                                "🔥 AGGRESSIVE", "Task re-enabled", "Enabled state changes", 
                                "FORCE RESET", "Schedule changed", "Aggressive update"
                            ]):
                                print(f"🎯 Detected aggressive reset activity!")
                                
                except Exception:
                    pass
            
            status = self.get_task_status()
            print(f"⏱️  Check #{i+1}: enabled={status['enabled']}, last_run={status['last_run']}, next_run={status['next_run']}")
            
            # 如果 next_run 被设置，说明任务已经被重新调度
            if status and status['next_run']:
                print(f"🎉 SUCCESS! Task rescheduled with next_run: {status['next_run']}")
                return True
        
        print("❌ FAILED: Task was not rescheduled within 60 seconds")
        return False
    
    def test_parameter_update(self):
        """🔥 测试参数更新检测"""
        print("\n" + "="*60)
        print("🔥 TEST 2: PARAMETER UPDATE DETECTION")
        print("="*60)
        
        # 确保任务是启用状态
        with get_scheduler_db_session() as session:
            task = session.get(ScheduledTaskModel, self.test_task_id)
            if not task or not task.enabled:
                print("❌ Task is not enabled, skipping parameter test")
                return False
        
        print("🔄 Updating task parameters...")
        new_message = f"updated_at_{datetime.now().strftime('%H%M%S')}"
        
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, self.test_task_id)
                if task:
                    # 🔥 更新参数
                    task.parameters = {"operation": "test", "message": new_message}
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
                    print(f"✅ Updated parameters: {task.parameters}")
        except Exception as e:
            print(f"❌ Failed to update parameters: {e}")
            return False
        
        # 等待检测
        print("⏳ Waiting for parameter change detection...")
        for i in range(8):  # 40秒等待
            time.sleep(5)
            
            # 检查日志
            if self.beat_process:
                try:
                    import select
                    if select.select([self.beat_process.stdout], [], [], 0.1)[0]:
                        output = self.beat_process.stdout.readline()
                        if output:
                            print(f"📜 Beat: {output.strip()}")
                            if "🔥 Content hash changed" in output:
                                print("🎯 Parameter change detected!")
                                return True
                except Exception:
                    pass
            
            print(f"⏱️  Check #{i+1}: waiting for content hash change detection...")
        
        print("❌ FAILED: Parameter change was not detected within 40 seconds")
        return False
    
    def test_schedule_modification(self):
        """🔥 测试调度配置修改"""
        print("\n" + "="*60)
        print("🔥 TEST 3: SCHEDULE CONFIGURATION MODIFICATION")
        print("="*60)
        
        print("🔄 Modifying schedule configuration...")
        
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, self.test_task_id)
                if task:
                    # 🔥 修改调度间隔
                    task.schedule_config = {"interval": 60}  # 改为60秒
                    task.priority = 10  # 修改优先级
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
                    print(f"✅ Updated schedule config: {task.schedule_config}, priority: {task.priority}")
        except Exception as e:
            print(f"❌ Failed to update schedule: {e}")
            return False
        
        # 等待检测
        print("⏳ Waiting for schedule change detection...")
        for i in range(6):  # 30秒等待
            time.sleep(5)
            
            if self.beat_process:
                try:
                    import select
                    if select.select([self.beat_process.stdout], [], [], 0.1)[0]:
                        output = self.beat_process.stdout.readline()
                        if output:
                            print(f"📜 Beat: {output.strip()}")
                            if any(keyword in output for keyword in [
                                "🔥 Content hash changed", "🔥 AGGRESSIVE schedule change"
                            ]):
                                print("🎯 Schedule change detected!")
                                return True
                except Exception:
                    pass
            
            print(f"⏱️  Check #{i+1}: waiting for schedule change detection...")
        
        print("❌ FAILED: Schedule change was not detected within 30 seconds")
        return False
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🔥" * 30)
        print("🔥 AGGRESSIVE RESET COMPREHENSIVE TEST")
        print("🔥" * 30)
        
        success_count = 0
        total_tests = 3
        
        try:
            # 设置环境
            self.setup_test_environment()
            
            # 启动 Beat
            if not self.start_beat_process():
                print("❌ Failed to start beat process")
                return
            
            # 等待初始化
            print("⏳ Waiting for scheduler initialization...")
            time.sleep(5)
            
            # 测试 1: enabled 0->1
            if self.test_enabled_0_to_1_transition():
                success_count += 1
                print("✅ TEST 1 PASSED")
            else:
                print("❌ TEST 1 FAILED")
            
            time.sleep(3)
            
            # 测试 2: 参数更新
            if self.test_parameter_update():
                success_count += 1
                print("✅ TEST 2 PASSED")
            else:
                print("❌ TEST 2 FAILED")
            
            time.sleep(3)
            
            # 测试 3: 调度修改
            if self.test_schedule_modification():
                success_count += 1
                print("✅ TEST 3 PASSED")
            else:
                print("❌ TEST 3 FAILED")
            
        finally:
            # 清理
            self.stop_beat_process()
            self.cleanup_test_task()
        
        # 结果报告
        print("\n" + "🔥" * 50)
        print(f"🔥 AGGRESSIVE RESET TEST RESULTS")
        print(f"🔥 PASSED: {success_count}/{total_tests}")
        print(f"🔥 SUCCESS RATE: {success_count/total_tests*100:.1f}%")
        print("🔥" * 50)
        
        if success_count == total_tests:
            print("🎉 ALL TESTS PASSED! Aggressive reset mechanism is working!")
        else:
            print("💥 SOME TESTS FAILED! Need further investigation.")
            
        return success_count == total_tests


def main():
    """主测试函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
🔥 Aggressive Reset Test Script

This script tests the aggressive reset mechanism in DatabaseScheduler v3:

1. enabled 0->1 transition detection and rescheduling
2. Parameter update detection and reload
3. Schedule configuration change detection

Usage:
    python test_aggressive_reset.py

Requirements:
    - Database tables created (run create_tables.py)
    - Redis/RabbitMQ running
    - No other Celery Beat instances running
        """)
        return
    
    print("🔥 Starting Aggressive Reset Mechanism Test...")
    
    tester = AggressiveResetTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Aggressive reset mechanism is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Aggressive reset mechanism needs fixes!")
        sys.exit(1)


if __name__ == "__main__":
    main() 