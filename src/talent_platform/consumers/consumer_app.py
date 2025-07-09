"""
Canal消费者应用启动器
"""

import argparse
import signal
import sys
import time
import json
from typing import Dict, Any

from talent_platform.logger import logger
from .consumer_manager import consumer_manager


def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        consumer_manager.stop_consuming()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def start_consumer(host: str = '127.0.0.1', port: int = 11111, 
                  destination: str = 'example', username: str = '', password: str = '',
                  batch_size: int = 100, timeout: int = 1):
    """启动Canal消费者"""
    logger.info("Starting Canal consumer service...")
    
    # 设置信号处理器
    setup_signal_handlers()
    
    try:
        # 加载默认消费者
        consumer_manager.load_default_consumers()
        
        # 配置Canal客户端
        success = consumer_manager.setup_canal_client(host, port, destination, username, password)
        if not success:
            logger.error("Failed to setup Canal client")
            return False
        
        # 开始消费
        success = consumer_manager.start_consuming(batch_size, timeout)
        if not success:
            logger.error("Failed to start consuming")
            return False
        
        logger.info("Canal consumer service started successfully")
        
        # 保持运行
        try:
            while consumer_manager.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
    except Exception as e:
        logger.error(f"Error in consumer service: {e}")
        return False
    finally:
        consumer_manager.stop_consuming()
        logger.info("Canal consumer service stopped")
    
    return True


def stop_consumer():
    """停止Canal消费者"""
    logger.info("Stopping Canal consumer service...")
    consumer_manager.stop_consuming()
    print("Canal consumer service stopped")


def list_consumers():
    """列出所有消费者"""
    try:
        consumers = consumer_manager.list_consumers()
        
        print(f"\n{'='*60}")
        print(f"消费者列表 (共 {len(consumers)} 个)")
        print(f"{'='*60}")
        
        for consumer in consumers:
            status = "✓ 启用" if consumer["enabled"] else "✗ 禁用"
            print(f"名称: {consumer['name']}")
            print(f"状态: {status}")
            print(f"过滤器数量: {len(consumer['filters'])}")
            
            if consumer['filters']:
                print("监听表:")
                for filter_info in consumer['filters']:
                    events = ', '.join(filter_info['event_types'])
                    print(f"  - {filter_info['database']}.{filter_info['table']} ({events})")
            
            print("-" * 40)
        
    except Exception as e:
        logger.error(f"List consumers failed: {e}")
        print(f"获取消费者列表失败: {e}")


def enable_consumer(consumer_name: str):
    """启用消费者"""
    try:
        success = consumer_manager.enable_consumer(consumer_name)
        
        if success:
            print(f"\n✓ 消费者 '{consumer_name}' 已启用")
        else:
            print(f"\n✗ 消费者 '{consumer_name}' 不存在")
            
    except Exception as e:
        logger.error(f"Enable consumer failed: {e}")
        print(f"启用消费者失败: {e}")


def disable_consumer(consumer_name: str):
    """禁用消费者"""
    try:
        success = consumer_manager.disable_consumer(consumer_name)
        
        if success:
            print(f"\n✓ 消费者 '{consumer_name}' 已禁用")
        else:
            print(f"\n✗ 消费者 '{consumer_name}' 不存在")
            
    except Exception as e:
        logger.error(f"Disable consumer failed: {e}")
        print(f"禁用消费者失败: {e}")


def get_status():
    """获取系统状态"""
    try:
        status = consumer_manager.get_status()
        
        print(f"\n{'='*60}")
        print(f"Canal消费者系统状态")
        print(f"{'='*60}")
        print(f"运行状态: {'✓ 运行中' if status['running'] else '✗ 未运行'}")
        print(f"Canal连接: {'✓ 已连接' if status['canal_connected'] else '✗ 未连接'}")
        print(f"消费者总数: {status['total_consumers']}")
        print(f"启用消费者: {status['enabled_consumers']}")
        
        if status['consumers']:
            print(f"\n消费者详情:")
            for consumer in status['consumers']:
                status_text = "启用" if consumer["enabled"] else "禁用"
                print(f"  - {consumer['name']}: {status_text} ({len(consumer['filters'])} 个过滤器)")
        
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        print(f"获取状态失败: {e}")


def test_consumer(consumer_name: str):
    """测试消费者（模拟事件）"""
    try:
        consumer = consumer_manager.get_consumer(consumer_name)
        if not consumer:
            print(f"\n✗ 消费者 '{consumer_name}' 不存在")
            return
        
        # 创建测试事件
        from .canal_client import ChangeEvent
        from datetime import datetime
        
        test_event = ChangeEvent(
            database="test_db",
            table="test_table",
            event_type="INSERT",
            data={"id": 1, "name": "test", "email": "test@example.com"},
            timestamp=datetime.now()
        )
        
        print(f"\n📋 测试消费者: {consumer_name}")
        print(f"模拟事件: {test_event.database}.{test_event.table} - {test_event.event_type}")
        
        # 处理测试事件
        consumer.handle_event(test_event)
        
        print(f"✓ 测试完成")
        
    except Exception as e:
        logger.error(f"Test consumer failed: {e}")
        print(f"测试消费者失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Canal消费者系统管理工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 启动消费者命令
    start_parser = subparsers.add_parser('start', help='启动Canal消费者')
    start_parser.add_argument('--host', default='127.0.0.1', help='Canal服务器地址')
    start_parser.add_argument('--port', type=int, default=11111, help='Canal服务器端口')
    start_parser.add_argument('--destination', default='example', help='Canal destination')
    start_parser.add_argument('--username', default='', help='Canal用户名')
    start_parser.add_argument('--password', default='', help='Canal密码')
    start_parser.add_argument('--batch-size', type=int, default=100, help='批处理大小')
    start_parser.add_argument('--timeout', type=int, default=1, help='超时时间(秒)')
    
    # 停止消费者命令
    subparsers.add_parser('stop', help='停止Canal消费者')
    
    # 列出消费者命令
    subparsers.add_parser('list', help='列出所有消费者')
    
    # 消费者管理命令
    enable_parser = subparsers.add_parser('enable', help='启用消费者')
    enable_parser.add_argument('consumer_name', help='消费者名称')
    
    disable_parser = subparsers.add_parser('disable', help='禁用消费者')
    disable_parser.add_argument('consumer_name', help='消费者名称')
    
    # 状态命令
    subparsers.add_parser('status', help='获取系统状态')
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试消费者')
    test_parser.add_argument('consumer_name', help='消费者名称')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        start_consumer(
            host=args.host,
            port=args.port,
            destination=args.destination,
            username=args.username,
            password=args.password,
            batch_size=args.batch_size,
            timeout=args.timeout
        )
    elif args.command == 'stop':
        stop_consumer()
    elif args.command == 'list':
        list_consumers()
    elif args.command == 'enable':
        enable_consumer(args.consumer_name)
    elif args.command == 'disable':
        disable_consumer(args.consumer_name)
    elif args.command == 'status':
        get_status()
    elif args.command == 'test':
        test_consumer(args.consumer_name)
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 