#!/usr/bin/env python3
"""
调度系统启动脚本
"""

import sys
import argparse
from talent_platform.scheduler import celery_app, TaskScheduler, PluginManager
from talent_platform.logger import logger


def start_worker(queues=None, concurrency=None):
    """启动 Celery Worker"""
    logger.info("Starting Celery Worker...")
    
    argv = ['worker', '--loglevel=info']
    
    if queues:
        argv.extend(['--queues', queues])
    else:
        argv.extend(['--queues', 'plugin_tasks,monitoring,high_priority'])
    
    if concurrency:
        argv.extend(['--concurrency', str(concurrency)])
    
    celery_app.start(argv)


def start_beat():
    """启动 Celery Beat (定时任务调度器)"""
    logger.info("Starting Celery Beat...")
    
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
        test_params = {"operation": operation or "sync_data"}
        
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
        plugin_params = {"operation": operation or "sync_data", "index_name": "aaas"}
        plugin_params.update(params)
        
        # 触发执行
        task_id = task_scheduler.trigger_plugin(plugin_name, plugin_params)
        
        print(f"\n插件 '{plugin_name}' 已触发执行")
        print(f"任务ID: {task_id}")
        print(f"参数: {plugin_params}")
        
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='调度系统管理工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # Worker 命令
    worker_parser = subparsers.add_parser('worker', help='启动 Celery Worker')
    worker_parser.add_argument('--queues', help='指定队列')
    worker_parser.add_argument('--concurrency', type=int, help='并发数')
    
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
    
    # 热加载命令
    reload_parser = subparsers.add_parser('reload', help='重新加载插件')
    reload_parser.add_argument('plugin_name', help='插件名称')
    
    subparsers.add_parser('enable-hot-reload', help='启用热加载功能')
    subparsers.add_parser('disable-hot-reload', help='禁用热加载功能')
    subparsers.add_parser('watch', help='监听插件变更')
    
    # 健康检查命令
    subparsers.add_parser('health', help='系统健康检查')
    
    args = parser.parse_args()
    
    if args.command == 'worker':
        start_worker(args.queues, args.concurrency)
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
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 