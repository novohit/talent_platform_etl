#!/usr/bin/env python3
"""
调度系统启动脚本
"""

import sys
import os
import argparse
from talent_platform.scheduler import celery_app, TaskScheduler, PluginManager
from talent_platform.logger import logger


def start_worker(queues=None, concurrency=None, worker_name=None):
    """启动 Celery Worker"""
    logger.info("Starting Celery Worker...")
    
    argv = ['worker', '--loglevel=info', '-E']
    
    if queues:
        argv.extend(['--queues', queues])
    else:
        argv.extend(['--queues', 'plugin_tasks,monitoring,high_priority'])
    
    if concurrency:
        argv.extend(['--concurrency', str(concurrency)])
    
    # 添加worker名称支持
    if worker_name:
        # 如果提供了名称，使用用户指定的名称
        argv.extend(['-n', f'{worker_name}@%h'])
        logger.info(f"Starting worker with name: {worker_name}@%h")
    else:
        # 如果没有提供名称，使用默认名称（避免冲突）
        import os
        default_name = f"worker-{os.getpid()}"  # 使用进程ID确保唯一性
        argv.extend(['-n', f'{default_name}@%h'])
        logger.info(f"Starting worker with auto-generated name: {default_name}@%h")
    
    celery_app.start(argv)


def start_beat():
    """启动 Celery Beat (定时任务调度器)"""
    logger.info("Starting Celery Beat...")
    
    # 设置 SQL_ECHO env 为 False
    os.environ['SQL_ECHO'] = 'False'
    argv = ['beat', '--loglevel=info']
    celery_app.start(argv)


def start_monitor():
    """启动 Celery 监控"""
    logger.info("Starting Celery Monitor...")
    
    argv = ['events', '--loglevel=info']
    celery_app.start(argv)


def list_plugins():
    """列出所有插件"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    plugins = plugin_manager.list_plugins()
    
    print(f"\n{'='*60}")
    print(f"插件列表 (共 {len(plugins)} 个)")
    print(f"{'='*60}")
    
    for plugin in plugins:
        status = "✓ 已启用" if plugin["enabled"] else "✗ 已禁用"
        print(f"名称: {plugin['name']}")
        print(f"版本: {plugin['version']}")
        print(f"状态: {status}")
        print(f"描述: {plugin['description']}")
        print(f"入口: {plugin['entry_point']}")
        print(f"依赖: {', '.join(plugin['dependencies'])}")
        print(f"标签: {', '.join(plugin['tags'])}")
        print("-" * 40)


def list_plugins_hot():
    """列出所有插件及热加载信息"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    plugins = plugin_manager.list_plugins_with_hot_info()
    
    print(f"\n{'='*80}")
    print(f"插件热加载状态 (共 {len(plugins)} 个)")
    print(f"{'='*80}")
    
    for plugin in plugins:
        metadata = plugin.get('metadata')
        if not metadata:
            continue
            
        status = "✓ 已启用" if metadata.enabled else "✗ 已禁用"
        loaded = "✓ 已加载" if plugin["loaded"] else "✗ 未加载"
        has_updates = "⚠ 有更新" if plugin["has_updates"] else "✓ 最新"
        
        print(f"名称: {metadata.name}")
        print(f"版本: {metadata.version}")
        print(f"状态: {status}")
        print(f"加载: {loaded}")
        print(f"更新: {has_updates}")
        
        if plugin["load_time"]:
            print(f"加载时间: {plugin['load_time']}")
        if plugin["checksum"]:
            print(f"校验和: {plugin['checksum'][:8]}...")
        
        print(f"热加载: {'✓ 启用' if plugin_manager.enable_hot_reload else '✗ 禁用'}")
        print("-" * 40)


def reload_plugin(plugin_name):
    """重新加载插件"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    logger.info(f"Reloading plugin: {plugin_name}")
    
    try:
        success = plugin_manager.force_reload_plugin(plugin_name)
        
        if success:
            print(f"\n✓ 插件 '{plugin_name}' 重新加载成功")
        else:
            print(f"\n✗ 插件 '{plugin_name}' 重新加载失败")
            
    except Exception as e:
        logger.error(f"Plugin reload failed: {e}")
        print(f"\n✗ 插件重新加载失败: {e}")


def enable_hot_reload():
    """启用热加载功能"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    try:
        plugin_manager.enable_hot_loading()
        print("\n✓ 插件热加载已启用")
        print("系统将自动监听插件文件变更并重新加载")
        
    except Exception as e:
        logger.error(f"Failed to enable hot reload: {e}")
        print(f"\n✗ 启用热加载失败: {e}")


def disable_hot_reload():
    """禁用热加载功能"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    try:
        plugin_manager.disable_hot_loading()
        print("\n✓ 插件热加载已禁用")
        
    except Exception as e:
        logger.error(f"Failed to disable hot reload: {e}")
        print(f"\n✗ 禁用热加载失败: {e}")


def watch_plugins():
    """监听插件变更（阻塞模式）"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    print("开始监听插件变更... (按 Ctrl+C 停止)")
    
    try:
        if not plugin_manager.enable_hot_reload:
            plugin_manager.enable_hot_loading()
        
        # 保持运行
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n停止监听插件变更")
        plugin_manager.disable_hot_loading()
    except Exception as e:
        logger.error(f"Error in plugin watching: {e}")
        print(f"\n监听失败: {e}")


def test_plugin(plugin_name, operation=None):
    """测试插件"""
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    logger.info(f"Testing plugin: {plugin_name}")
    
    try:
        # 准备测试参数
        test_params = {"operation": operation or ""}
        
        if plugin_name == "data_processor":
            test_params.update({
                "sync_type": "manual",
                "teacher_id": "test_teacher_123"
            })
        elif plugin_name == "es_indexer":
            test_params.update({
                "index_name": "test_index",
                "teacher_id": "test_teacher_123",
                "data": {
                    "school_name": "Test University",
                    "derived_teacher_name": "Test Teacher",
                    "is_valid": True
                }
            })
        
        # 执行插件
        result = plugin_manager.execute_plugin(plugin_name, **test_params)
        
        print(f"\n{'='*60}")
        print(f"插件测试结果: {plugin_name}")
        print(f"{'='*60}")
        print(f"状态: {result.get('status', 'unknown')}")
        print(f"操作: {result.get('operation', 'unknown')}")
        print(f"时间: {result.get('timestamp', 'unknown')}")
        
        if result.get('result'):
            print(f"结果:")
            import json
            print(json.dumps(result['result'], indent=2, ensure_ascii=False))
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        
    except Exception as e:
        logger.error(f"Plugin test failed: {e}")
        print(f"测试失败: {e}")


def trigger_plugin(plugin_name, operation=None, **params):
    """触发插件执行"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    logger.info(f"Triggering plugin: {plugin_name}")
    
    try:
        # 准备参数
        # plugin_params = {"operation": operation or "sync_data"}
        plugin_params = {}
        plugin_params.update(params)
        
        # 触发执行
        task_id = task_scheduler.trigger_plugin(plugin_name, plugin_params)
        
        print(f"\n✓ 插件 '{plugin_name}' 已触发执行")
        print(f"任务ID: {task_id}")
        print(f"参数: {plugin_params}")
        print()
        print("📝 取消任务的方法:")
        print(f"   python -m talent_platform.scheduler_app cancel {task_id}")
        print(f"   或者: python -m talent_platform.scheduler_app cancel-plugin {plugin_name}")
        print()
        print("🔍 查看任务状态:")
        print(f"   python -m talent_platform.scheduler_app status {task_id}")
        
        return task_id
        
    except Exception as e:
        logger.error(f"Plugin trigger failed: {e}")
        print(f"触发失败: {e}")


def get_task_status(task_id):
    """获取任务状态"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        status = task_scheduler.get_task_status(task_id)
        
        print(f"\n{'='*60}")
        print(f"任务状态: {task_id}")
        print(f"{'='*60}")
        print(f"状态: {status['status']}")
        
        if status.get('result'):
            print(f"结果:")
            import json
            print(json.dumps(status['result'], indent=2, ensure_ascii=False))
        
        if status.get('traceback'):
            print(f"错误追踪: {status['traceback']}")
            
    except Exception as e:
        logger.error(f"Get task status failed: {e}")
        print(f"获取状态失败: {e}")


def cancel_task(task_id):
    """取消任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        result = task_scheduler.cancel_task(task_id)
        
        print(f"\n{'='*60}")
        print(f"取消任务: {task_id}")
        print(f"{'='*60}")
        
        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result['message']}")
            if result.get('status'):
                print(f"任务状态: {result['status']}")
                
    except Exception as e:
        logger.error(f"Cancel task failed: {e}")
        print(f"取消任务失败: {e}")


def list_active_tasks():
    """列出活动任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        result = task_scheduler.list_active_tasks()
        
        print(f"\n{'='*60}")
        print(f"活动任务列表")
        print(f"{'='*60}")
        print(f"Worker 数量: {result['total_workers']}")
        print(f"任务总数: {result['total_tasks']}")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
            return
        
        if result['total_tasks'] == 0:
            print("当前没有活动任务")
            return
        
        print()
        for worker, tasks in result['active_tasks'].items():
            print(f"Worker: {worker}")
            print(f"任务数: {len(tasks)}")
            print("-" * 40)
            
            for task in tasks:
                task_id = task['id']
                task_name = task.get('name', 'Unknown')
                args = task.get('args', [])
                
                print(f"  任务ID: {task_id}")
                print(f"  任务名: {task_name}")
                
                # 如果是插件任务，显示插件名
                if (task_name == 'talent_platform.scheduler.tasks.execute_plugin_task' and 
                    len(args) > 0):
                    print(f"  插件名: {args[0]}")
                
                if args:
                    print(f"  参数: {args}")
                
                print()
            
            print("=" * 40)
            
    except Exception as e:
        logger.error(f"List active tasks failed: {e}")
        print(f"获取活动任务列表失败: {e}")


def cancel_plugin_tasks(plugin_name):
    """取消指定插件的所有任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        result = task_scheduler.cancel_all_plugin_tasks(plugin_name)
        
        print(f"\n{'='*60}")
        print(f"取消插件任务: {plugin_name}")
        print(f"{'='*60}")
        
        if result['success']:
            print(f"✓ {result['message']}")
            if result.get('cancelled_tasks'):
                print("已取消的任务ID:")
                for task_id in result['cancelled_tasks']:
                    print(f"  - {task_id}")
        else:
            print(f"✗ {result['message']}")
                
    except Exception as e:
        logger.error(f"Cancel plugin tasks failed: {e}")
        print(f"取消插件任务失败: {e}")


def health_check():
    """系统健康检查"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    from talent_platform.scheduler.plugin_manager import plugin_manager
    
    try:
        status = task_scheduler.health_check()
        
        print(f"\n{'='*60}")
        print(f"系统健康检查")
        print(f"{'='*60}")
        print(f"调度器状态: {status['scheduler_status']}")
        print(f"总插件数: {status['total_plugins']}")
        print(f"已启用插件: {status['enabled_plugins']}")
        print(f"调度任务数: {status['scheduled_tasks']}")
        print(f"活动任务数: {status['active_tasks']}")
        print(f"热加载状态: {'✓ 启用' if plugin_manager.enable_hot_reload else '✗ 禁用'}")
        print(f"检查时间: {status['timestamp']}")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"健康检查失败: {e}")


def list_scheduled_tasks():
    """列出所有定时任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        tasks = task_scheduler.get_scheduled_tasks()
        
        print(f"\n{'='*60}")
        print(f"定时任务列表 (共 {len(tasks)} 个)")
        print(f"{'='*60}")
        
        for task in tasks:
            status = "✓ 启用" if task["enabled"] else "✗ 禁用"
            print(f"ID: {task['id']}")
            print(f"名称: {task['name']}")
            print(f"插件: {task['plugin_name']}")
            print(f"状态: {status}")
            print(f"调度类型: {task['schedule_type']}")
            print(f"调度配置: {task['schedule_config']}")
            print(f"参数: {task['parameters']}")
            
            if task.get('last_run'):
                print(f"上次运行: {task['last_run']}")
            if task.get('next_run'):
                print(f"下次运行: {task['next_run']}")
            
            print("-" * 40)
        
    except Exception as e:
        logger.error(f"List scheduled tasks failed: {e}")
        print(f"获取定时任务列表失败: {e}")


def add_scheduled_task(plugin_name, task_id=None, schedule_type="interval", schedule_config=None, **params):
    """添加定时任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        if not task_id:
            task_id = f"{plugin_name}_{schedule_type}_task"
        
        if not schedule_config:
            if schedule_type == "interval":
                schedule_config = {"interval": 3600}  # 默认1小时
            elif schedule_type == "cron":
                schedule_config = {"cron": "0 * * * *"}  # 默认每小时
        
        task_config = {
            "id": task_id,
            "name": f"{plugin_name} 定时任务",
            "plugin_name": plugin_name,
            "parameters": params,
            "schedule_type": schedule_type,
            "schedule_config": schedule_config
        }
        
        success = task_scheduler.add_scheduled_task(task_config)
        
        if success:
            print(f"\n✓ 定时任务添加成功")
            print(f"任务ID: {task_id}")
            print(f"插件: {plugin_name}")
            print(f"调度类型: {schedule_type}")
            print(f"调度配置: {schedule_config}")
        else:
            print(f"\n✗ 定时任务添加失败")
            
    except Exception as e:
        logger.error(f"Add scheduled task failed: {e}")
        print(f"添加定时任务失败: {e}")


def remove_scheduled_task(task_id):
    """移除定时任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        success = task_scheduler.remove_scheduled_task(task_id)
        
        if success:
            print(f"\n✓ 定时任务 '{task_id}' 已移除")
        else:
            print(f"\n✗ 定时任务 '{task_id}' 不存在")
            
    except Exception as e:
        logger.error(f"Remove scheduled task failed: {e}")
        print(f"移除定时任务失败: {e}")


def enable_scheduled_task(task_id):
    """启用定时任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        success = task_scheduler.enable_task(task_id)
        
        if success:
            print(f"\n✓ 定时任务 '{task_id}' 已启用")
        else:
            print(f"\n✗ 定时任务 '{task_id}' 不存在")
            
    except Exception as e:
        logger.error(f"Enable scheduled task failed: {e}")
        print(f"启用定时任务失败: {e}")


def disable_scheduled_task(task_id):
    """禁用定时任务"""
    from talent_platform.scheduler.task_scheduler import task_scheduler
    
    try:
        success = task_scheduler.disable_task(task_id)
        
        if success:
            print(f"\n✓ 定时任务 '{task_id}' 已禁用")
        else:
            print(f"\n✗ 定时任务 '{task_id}' 不存在")
            
    except Exception as e:
        logger.error(f"Disable scheduled task failed: {e}")
        print(f"禁用定时任务失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='调度系统管理工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # Worker 命令
    worker_parser = subparsers.add_parser('worker', help='启动 Celery Worker')
    worker_parser.add_argument('--queues', help='指定队列')
    worker_parser.add_argument('--concurrency', type=int, help='并发数')
    worker_parser.add_argument('--name', help='Worker名称 (用于区分多个Worker)')
    
    # Beat 命令
    subparsers.add_parser('beat', help='启动 Celery Beat')
    
    # Monitor 命令
    subparsers.add_parser('monitor', help='启动 Celery 监控')
    
    # 插件命令
    subparsers.add_parser('list-plugins', help='列出所有插件')
    subparsers.add_parser('list-plugins-hot', help='列出所有插件及热加载状态')
    
    test_parser = subparsers.add_parser('test-plugin', help='测试插件')
    test_parser.add_argument('plugin_name', help='插件名称')
    test_parser.add_argument('--operation', help='操作类型')
    
    trigger_parser = subparsers.add_parser('trigger', help='触发插件执行')
    trigger_parser.add_argument('plugin_name', help='插件名称')
    trigger_parser.add_argument('--operation', help='操作类型')
    
    status_parser = subparsers.add_parser('status', help='获取任务状态')
    status_parser.add_argument('task_id', help='任务ID')
    
    # 任务取消命令
    cancel_parser = subparsers.add_parser('cancel', help='取消运行中的任务')
    cancel_parser.add_argument('task_id', help='任务ID')
    
    # 列出活动任务命令
    subparsers.add_parser('list-active', help='列出所有活动任务')
    
    # 取消插件任务命令
    cancel_plugin_parser = subparsers.add_parser('cancel-plugin', help='取消指定插件的所有任务')
    cancel_plugin_parser.add_argument('plugin_name', help='插件名称')
    
    # 热加载命令
    reload_parser = subparsers.add_parser('reload', help='重新加载插件')
    reload_parser.add_argument('plugin_name', help='插件名称')
    
    subparsers.add_parser('enable-hot-reload', help='启用热加载功能')
    subparsers.add_parser('disable-hot-reload', help='禁用热加载功能')
    subparsers.add_parser('watch', help='监听插件变更')
    
    # 健康检查命令
    subparsers.add_parser('health', help='系统健康检查')
    
    # 定时任务管理命令
    subparsers.add_parser('list-tasks', help='列出所有定时任务')
    
    add_task_parser = subparsers.add_parser('add-task', help='添加定时任务')
    add_task_parser.add_argument('plugin_name', help='插件名称')
    add_task_parser.add_argument('--task-id', help='任务ID')
    add_task_parser.add_argument('--schedule-type', choices=['interval', 'cron'], default='interval', help='调度类型')
    add_task_parser.add_argument('--interval', type=int, help='间隔时间（秒）')
    add_task_parser.add_argument('--cron', help='Cron表达式')
    add_task_parser.add_argument('--operation', help='操作类型')
    
    remove_task_parser = subparsers.add_parser('remove-task', help='移除定时任务')
    remove_task_parser.add_argument('task_id', help='任务ID')
    
    enable_task_parser = subparsers.add_parser('enable-task', help='启用定时任务')
    enable_task_parser.add_argument('task_id', help='任务ID')
    
    disable_task_parser = subparsers.add_parser('disable-task', help='禁用定时任务')
    disable_task_parser.add_argument('task_id', help='任务ID')
    
    args = parser.parse_args()
    
    if args.command == 'worker':
        start_worker(args.queues, args.concurrency, args.name)
    elif args.command == 'beat':
        start_beat()
    elif args.command == 'monitor':
        start_monitor()
    elif args.command == 'list-plugins':
        list_plugins()
    elif args.command == 'list-plugins-hot':
        list_plugins_hot()
    elif args.command == 'test-plugin':
        test_plugin(args.plugin_name, args.operation)
    elif args.command == 'trigger':
        trigger_plugin(args.plugin_name, args.operation)
    elif args.command == 'status':
        get_task_status(args.task_id)
    elif args.command == 'cancel':
        cancel_task(args.task_id)
    elif args.command == 'list-active':
        list_active_tasks()
    elif args.command == 'cancel-plugin':
        cancel_plugin_tasks(args.plugin_name)
    elif args.command == 'reload':
        reload_plugin(args.plugin_name)
    elif args.command == 'enable-hot-reload':
        enable_hot_reload()
    elif args.command == 'disable-hot-reload':
        disable_hot_reload()
    elif args.command == 'watch':
        watch_plugins()
    elif args.command == 'health':
        health_check()
    elif args.command == 'list-tasks':
        list_scheduled_tasks()
    elif args.command == 'add-task':
        schedule_config = None
        params = {}
        
        if args.operation:
            params['operation'] = args.operation
        
        if args.schedule_type == 'interval':
            interval = args.interval or 3600  # 默认1小时
            schedule_config = {"interval": interval}
        elif args.schedule_type == 'cron':
            cron = args.cron or "0 * * * *"  # 默认每小时
            schedule_config = {"cron": cron}
        
        add_scheduled_task(args.plugin_name, args.task_id, args.schedule_type, schedule_config, **params)
    elif args.command == 'remove-task':
        remove_scheduled_task(args.task_id)
    elif args.command == 'enable-task':
        enable_scheduled_task(args.task_id)
    elif args.command == 'disable-task':
        disable_scheduled_task(args.task_id)
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 