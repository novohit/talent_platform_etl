"""
消费者管理器
"""

import threading
from typing import Dict, List, Any, Optional
from .canal_client import CanalClient, ChangeEvent
from .base_consumer import BaseConsumer
from talent_platform.logger import logger


class ConsumerManager:
    """消费者管理器 - 管理多个消费者和Canal客户端"""
    
    def __init__(self):
        self.consumers: Dict[str, BaseConsumer] = {}
        self.canal_client: Optional[CanalClient] = None
        self.running = False
        self._consumer_thread: Optional[threading.Thread] = None
    
    def register_consumer(self, consumer: BaseConsumer):
        """注册消费者"""
        self.consumers[consumer.name] = consumer
        logger.info(f"Registered consumer: {consumer.name}")
    
    def unregister_consumer(self, consumer_name: str):
        """注销消费者"""
        if consumer_name in self.consumers:
            del self.consumers[consumer_name]
            logger.info(f"Unregistered consumer: {consumer_name}")
        else:
            logger.warning(f"Consumer not found: {consumer_name}")
    
    def get_consumer(self, consumer_name: str) -> Optional[BaseConsumer]:
        """获取消费者"""
        return self.consumers.get(consumer_name)
    
    def list_consumers(self) -> List[Dict[str, Any]]:
        """列出所有消费者"""
        return [consumer.get_status() for consumer in self.consumers.values()]
    
    def enable_consumer(self, consumer_name: str) -> bool:
        """启用消费者"""
        consumer = self.get_consumer(consumer_name)
        if consumer:
            consumer.enable()
            return True
        return False
    
    def disable_consumer(self, consumer_name: str) -> bool:
        """禁用消费者"""
        consumer = self.get_consumer(consumer_name)
        if consumer:
            consumer.disable()
            return True
        return False
    
    def setup_canal_client(self, host: str = '127.0.0.1', port: int = 11111, 
                          destination: str = 'example', username: str = '', password: str = ''):
        """设置Canal客户端"""
        try:
            self.canal_client = CanalClient(host, port, destination, username, password)
            
            # 添加事件处理器
            self.canal_client.add_event_handler(self._handle_change_event)
            
            logger.info(f"Canal client configured: {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Canal client: {e}")
            return False
    
    def _handle_change_event(self, event: ChangeEvent):
        """处理数据库变更事件"""
        logger.debug(f"Received change event: {event.database}.{event.table} - {event.event_type}")
        
        # 分发事件给所有消费者
        for consumer in self.consumers.values():
            try:
                consumer.handle_event(event)
            except Exception as e:
                logger.error(f"Consumer {consumer.name} failed to handle event: {e}")
    
    def start_consuming(self, batch_size: int = 100, timeout: int = 1) -> bool:
        """开始消费消息"""
        if not self.canal_client:
            logger.error("Canal client not configured")
            return False
        
        if self.running:
            logger.warning("Consumer manager is already running")
            return False
        
        def _consume():
            try:
                logger.info("Starting Canal message consumption...")
                self.running = True
                self.canal_client.start_consuming(batch_size, timeout)
            except Exception as e:
                logger.error(f"Error in consumer thread: {e}")
            finally:
                self.running = False
        
        # 在单独线程中运行消费逻辑
        self._consumer_thread = threading.Thread(target=_consume, daemon=True)
        self._consumer_thread.start()
        
        logger.info("Consumer manager started")
        return True
    
    def stop_consuming(self):
        """停止消费消息"""
        if not self.running:
            logger.warning("Consumer manager is not running")
            return
        
        logger.info("Stopping consumer manager...")
        
        if self.canal_client:
            self.canal_client.stop_consuming()
        
        if self._consumer_thread and self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=10)
        
        self.running = False
        logger.info("Consumer manager stopped")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and (self.canal_client and self.canal_client.is_running())
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            'running': self.is_running(),
            'consumers': self.list_consumers(),
            'canal_connected': self.canal_client.connected if self.canal_client else False,
            'total_consumers': len(self.consumers),
            'enabled_consumers': len([c for c in self.consumers.values() if c.enabled])
        }
    
    def load_default_consumers(self):
        """加载默认消费者"""
        try:
            # 导入并注册默认消费者
            from .consumers.teacher_consumer import TeacherConsumer
            from .consumers.example_consumer import ExampleConsumer
            
            # 注册教师数据消费者
            teacher_consumer = TeacherConsumer()
            self.register_consumer(teacher_consumer)
            
            # 注册示例消费者（默认禁用）
            example_consumer = ExampleConsumer()
            example_consumer.disable()  # 默认禁用示例消费者
            self.register_consumer(example_consumer)
            
            logger.info("Default consumers loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load default consumers: {e}")


# 全局消费者管理器实例
consumer_manager = ConsumerManager() 