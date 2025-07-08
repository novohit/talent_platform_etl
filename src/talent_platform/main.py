from talent_platform.etl.operations import query_teachers
from talent_platform.services.es.teacher_service import TeacherService
from talent_platform.logger import logger

# 导入调度系统
from talent_platform.scheduler import task_scheduler, plugin_manager


def main():
    logger.info("Starting ETL process")
    try:
        print("Hello from talent-platform-etl!")
        print("=" * 60)
        print("调度系统演示")
        print("=" * 60)

        # 原有的业务逻辑示例
        result = TeacherService.remove_by_ids(
            teacher_ids=["6f12da6d-7a78-4b05-aaac-418a7aba7491"]
        )
        print(f"ES操作结果: {result}")

        teachers = query_teachers()
        invalid_count = 0
        for teacher in teachers:
            if not teacher.is_valid:
                invalid_count += 1
                if invalid_count <= 3:  # 只显示前3个
                    print(f"无效教师: {teacher.derived_teacher_name} from {teacher.school_name}")
        
        if invalid_count > 3:
            print(f"... 还有 {invalid_count - 3} 个无效教师")

        print("\n" + "=" * 60)
        print("调度系统功能演示")
        print("=" * 60)

        # 1. 显示插件列表
        print("\n1. 可用插件:")
        plugins = plugin_manager.list_plugins()
        for plugin in plugins:
            status = "✓ 已启用" if plugin["enabled"] else "✗ 已禁用"
            print(f"   - {plugin['name']} v{plugin['version']} ({status})")
            print(f"     描述: {plugin['description']}")

        # 2. 测试插件直接执行
        print("\n2. 测试插件直接执行:")
        try:
            result = plugin_manager.execute_plugin(
                "data_processor",
                operation="sync_data",
                sync_type="manual"
            )
            print(f"   data_processor 执行结果: {result['status']}")
            if result.get('result'):
                print(f"   处理记录数: {result['result'].get('records_processed', 0)}")
        except Exception as e:
            print(f"   插件执行失败: {e}")

        # 3. 异步任务触发
        print("\n3. 异步任务触发:")
        try:
            task_id = task_scheduler.trigger_plugin(
                "es_indexer",
                {
                    "operation": "update_teacher_index",
                    "teacher_id": "demo_teacher_123",
                    "data": {
                        "school_name": "示例大学",
                        "derived_teacher_name": "示例教师",
                        "is_valid": True
                    }
                }
            )
            print(f"   ES索引任务已触发，任务ID: {task_id}")
        except Exception as e:
            print(f"   任务触发失败: {e}")

        # 4. 系统健康检查
        print("\n4. 系统健康检查:")
        try:
            health = task_scheduler.health_check()
            print(f"   调度器状态: {health['scheduler_status']}")
            print(f"   总插件数: {health['total_plugins']}")
            print(f"   已启用插件: {health['enabled_plugins']}")
            print(f"   调度任务数: {health['scheduled_tasks']}")
        except Exception as e:
            print(f"   健康检查失败: {e}")

        # 5. 展示调度任务配置
        print("\n5. 调度任务配置:")
        scheduled_tasks = task_scheduler.get_scheduled_tasks()
        for task in scheduled_tasks:
            print(f"   - {task['name']} ({task['plugin_name']})")
            print(f"     调度类型: {task['schedule_type']}")
            if task['enabled']:
                print("     状态: ✓ 已启用")
            else:
                print("     状态: ✗ 已禁用")

        print("\n" + "=" * 60)
        print("使用说明")
        print("=" * 60)
        print("1. 启动调度系统:")
        print("   ./start_scheduler.sh start")
        print()
        print("2. 查看系统状态:")
        print("   ./start_scheduler.sh status")
        print()
        print("3. 测试插件:")
        print("   python -m talent_platform.scheduler_app test-plugin data_processor")
        print()
        print("4. 触发任务:")
        print("   python -m talent_platform.scheduler_app trigger es_indexer --operation bulk_index")
        print()
        print("5. 查看详细文档:")
        print("   cat SCHEDULER_USAGE.md")

        # Example of different log levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

        # Simulating an error
        # raise Exception("Sample error")

    except Exception as e:
        logger.error(f"Error occurred during ETL process: {str(e)}", exc_info=True)
        raise

    logger.info("ETL process completed successfully")


if __name__ == "__main__":
    main()
