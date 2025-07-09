#!/usr/bin/env python3
"""
🔧 堆初始化修复测试脚本

验证 DatabaseScheduler v3 的堆初始化修复是否解决了 AttributeError 问题
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.scheduler.task_scheduler import task_scheduler


def test_heap_initialization():
    """测试堆初始化是否正常"""
    print("🔧 测试堆初始化修复...")
    
    # 清理测试任务
    cleanup_test_tasks()
    
    # 创建一个测试任务
    test_task_id = "heap_fix_test"
    task_config = {
        "id": test_task_id,
        "name": "Heap Fix Test Task",
        "plugin_name": "mysql_test",
        "parameters": {"operation": "test"},
        "schedule_type": "interval",
        "schedule_config": {"interval": 60},
        "enabled": True,
        "description": "Test task for heap initialization fix"
    }
    
    try:
        task_scheduler.add_scheduled_task(task_config)
        print(f"✅ 创建测试任务成功: {test_task_id}")
    except Exception as e:
        print(f"❌ 创建测试任务失败: {e}")
        return False
    
    # 测试启动 Beat 进程
    print("\n🚀 测试 Beat 启动（10秒超时）...")
    
    cmd = [
        "celery", "-A", "src.talent_platform.scheduler.celery_app", 
        "beat", "--loglevel=info"
    ]
    
    try:
        # 启动 Beat 进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("📡 Beat 进程已启动，监控日志...")
        
        # 监控进程 10 秒
        success_indicators = []
        error_occurred = False
        
        for i in range(20):  # 10秒，每500ms检查一次
            time.sleep(0.5)
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                # 进程已退出
                return_code = process.returncode
                if return_code != 0:
                    print(f"❌ Beat 进程异常退出，返回码: {return_code}")
                    error_occurred = True
                    break
                else:
                    print("✅ Beat 进程正常退出")
                    break
            
            # 读取输出
            try:
                import select
                if select.select([process.stdout], [], [], 0.1)[0]:
                    line = process.stdout.readline()
                    if line:
                        print(f"📜 {line.strip()}")
                        
                        # 检查成功指标
                        if "🔥 DatabaseScheduler v3 (AGGRESSIVE) initialized" in line:
                            success_indicators.append("scheduler_init")
                        if "🚀 Initial schedule read" in line:
                            success_indicators.append("initial_read")
                        if "🔥 Building AGGRESSIVE schedule" in line:
                            success_indicators.append("schedule_build")
                        
                        # 检查错误
                        if "AttributeError" in line or "NoneType" in line:
                            print(f"❌ 检测到错误: {line.strip()}")
                            error_occurred = True
                            break
                        if "CRITICAL" in line or "ERROR" in line:
                            print(f"⚠️ 检测到严重问题: {line.strip()}")
            except Exception:
                pass
        
        # 终止进程
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            process.kill()
        
        # 评估结果
        print(f"\n📊 测试结果:")
        print(f"   成功指标: {success_indicators}")
        print(f"   错误发生: {error_occurred}")
        
        if error_occurred:
            print("❌ 测试失败：检测到错误")
            return False
        elif len(success_indicators) >= 2:  # 至少要有调度器初始化和schedule读取
            print("✅ 测试成功：Beat 启动正常，无 AttributeError")
            return True
        else:
            print("⚠️ 测试部分成功：Beat 启动但可能存在问题")
            return False
            
    except Exception as e:
        print(f"❌ 启动 Beat 进程失败: {e}")
        return False
    finally:
        # 清理
        cleanup_test_tasks()


def cleanup_test_tasks():
    """清理测试任务"""
    try:
        with get_scheduler_db_session() as session:
            test_tasks = session.query(ScheduledTaskModel).filter(
                ScheduledTaskModel.id.like('heap_fix_test%')
            ).all()
            for task in test_tasks:
                session.delete(task)
            session.commit()
            if test_tasks:
                print(f"🧹 清理了 {len(test_tasks)} 个测试任务")
    except Exception as e:
        print(f"⚠️ 清理测试任务失败: {e}")


def main():
    """主测试函数"""
    print("🔧" * 40)
    print("🔧 DatabaseScheduler v3 堆初始化修复测试")
    print("🔧" * 40)
    
    # 检查数据库连接
    try:
        with get_scheduler_db_session() as session:
            pass
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return 1
    
    # 运行测试
    success = test_heap_initialization()
    
    print("\n" + "🔧" * 40)
    if success:
        print("🎉 堆初始化修复测试成功！")
        print("✅ AttributeError 问题已解决")
        print("✅ Beat 可以正常启动")
        return 0
    else:
        print("💥 堆初始化修复测试失败！")
        print("❌ 仍然存在问题，需要进一步调试")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 