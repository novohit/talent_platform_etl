#!/usr/bin/env python3
"""
SQLModel 兼容性测试
验证 DatabaseScheduler 与 SQLModel 的兼容性
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.scheduler.database_scheduler import DatabaseScheduler
from talent_platform.logger import logger


def test_sqlmodel_compatibility():
    """测试 SQLModel 兼容性"""
    
    print("🧪 SQLModel 兼容性测试")
    print("=" * 50)
    
    try:
        # 1. 测试数据库连接
        print("\n📱 1. 测试数据库连接...")
        with get_scheduler_db_session() as session:
            # 测试查询
            tasks = session.query(ScheduledTaskModel).filter(
                ScheduledTaskModel.enabled == True
            ).all()
            print(f"   ✅ 成功查询到 {len(tasks)} 个启用的任务")
        
        # 2. 测试 func.max 查询
        print("\n📊 2. 测试变化检测查询...")
        with get_scheduler_db_session() as session:
            from sqlalchemy import func
            result = session.query(func.max(ScheduledTaskModel.updated_at)).scalar()
            print(f"   ✅ 最新更新时间: {result}")
            
        # 3. 测试 DatabaseScheduler 初始化
        print("\n🚀 3. 测试 DatabaseScheduler 初始化...")
        
        # 创建一个模拟 Celery app 对象
        class MockApp:
            class conf:
                @staticmethod
                def get(key, default=None):
                    configs = {
                        'beat_max_loop_interval': 5.0
                    }
                    return configs.get(key, default)
        
        mock_app = MockApp()
        scheduler = DatabaseScheduler(app=mock_app)
        print(f"   ✅ DatabaseScheduler 初始化成功，max_interval={scheduler.max_interval}s")
        
        # 4. 测试 schedule_changed 方法
        print("\n🔍 4. 测试变化检测方法...")
        changed = scheduler.schedule_changed()
        print(f"   ✅ schedule_changed() 返回: {changed}")
        
        # 5. 测试 all_as_schedule 方法
        print("\n📋 5. 测试调度表加载...")
        schedule_dict = scheduler.all_as_schedule()
        print(f"   ✅ 加载了 {len(schedule_dict)} 个调度任务")
        
        # 6. 测试 SQLModel 字段访问
        print("\n🔧 6. 测试 SQLModel 字段访问...")
        with get_scheduler_db_session() as session:
            tasks = session.query(ScheduledTaskModel).limit(3).all()
            for task in tasks:
                print(f"   📝 任务: {task.id} | 插件: {task.plugin_name} | 启用: {task.enabled}")
                # 测试 JSON 字段
                print(f"      参数: {task.parameters}")
                print(f"      调度配置: {task.schedule_config}")
        
        print("\n" + "=" * 50)
        print("🎉 SQLModel 兼容性测试全部通过！")
        
        print("\n✅ 兼容性验证结果:")
        print("   • SQLModel 查询语法正常")
        print("   • func.max() 聚合函数正常")
        print("   • JSON 字段访问正常")
        print("   • DatabaseScheduler 初始化正常")
        print("   • 变化检测机制正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ SQLModel 兼容性测试失败: {e}")
        logger.error(f"SQLModel compatibility test failed: {e}", exc_info=True)
        return False


def test_create_sqlmodel_task():
    """测试创建 SQLModel 任务"""
    
    print("\n🆕 额外测试：创建 SQLModel 任务...")
    
    try:
        with get_scheduler_db_session() as session:
            # 创建一个测试任务
            test_task = ScheduledTaskModel(
                id="sqlmodel_test_task",
                name="SQLModel兼容性测试任务",
                plugin_name="mysql_test",
                parameters={"operation": "health_check"},
                schedule_type="interval",
                schedule_config={"interval": 120},
                enabled=True,
                description="用于验证SQLModel兼容性的测试任务",
                priority=5,
                max_retries=3
            )
            
            # 检查是否已存在
            existing = session.query(ScheduledTaskModel).filter(
                ScheduledTaskModel.id == test_task.id
            ).first()
            
            if existing:
                print("   ℹ️  测试任务已存在，跳过创建")
            else:
                session.add(test_task)
                session.commit()
                print("   ✅ 成功创建 SQLModel 测试任务")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 创建 SQLModel 任务失败: {e}")
        return False


if __name__ == "__main__":
    try:
        print("🚀 开始 SQLModel 兼容性验证...")
        
        # 主要兼容性测试
        main_result = test_sqlmodel_compatibility()
        
        # 额外的创建测试
        create_result = test_create_sqlmodel_task()
        
        if main_result and create_result:
            print("\n🎊 所有 SQLModel 兼容性测试通过！")
            print("\n📚 相关信息:")
            print("   • SQLModel 是基于 SQLAlchemy 的现代 ORM")
            print("   • 我们的 DatabaseScheduler 完全兼容 SQLModel")
            print("   • 查询语法与 SQLAlchemy 保持一致")
            print("   • JSON 字段处理正常")
        else:
            print("\n⚠️  部分测试失败，请检查日志")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试中断")
    except Exception as e:
        logger.error(f"Compatibility test failed: {e}", exc_info=True)
        print(f"\n❌ 测试异常: {e}") 