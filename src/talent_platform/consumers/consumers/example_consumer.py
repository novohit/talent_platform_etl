"""
示例消费者实现
"""

from typing import Dict, Any
from ..base_consumer import BaseConsumer
from ..canal_client import ChangeEvent
from talent_platform.logger import logger


class ExampleConsumer(BaseConsumer):
    """示例消费者 - 展示如何实现自定义消费者"""
    
    def __init__(self):
        super().__init__("example_consumer")
        
        # 配置要监听的表
        # 示例：监听所有数据库的user表的INSERT和UPDATE事件
        self.add_filter("test_db", "users", {"INSERT", "UPDATE"})
        self.add_filter("test_db", "orders", {"INSERT"})
    
    def process_event(self, event: ChangeEvent):
        """处理数据库变更事件"""
        logger.info(f"ExampleConsumer received event: {event.database}.{event.table} - {event.event_type}")
        
        # 根据不同的表和事件类型调用不同的处理逻辑
        if event.table == "users":
            self._handle_user_change(event)
        elif event.table == "orders":
            self._handle_order_change(event)
        else:
            logger.debug(f"No specific handler for table: {event.table}")
    
    def _handle_user_change(self, event: ChangeEvent):
        """处理用户表变更"""
        if event.event_type == "INSERT":
            # 新用户注册，触发欢迎邮件插件
            user_data = event.data
            parameters = {
                "operation": "send_welcome_email",
                "user_id": user_data.get("id"),
                "email": user_data.get("email"),
                "username": user_data.get("username")
            }
            
            self.trigger_plugin("email_service", parameters, priority="normal")
            
        elif event.event_type == "UPDATE":
            # 用户信息更新，触发数据同步插件
            before_data = event.data.get("before", {})
            after_data = event.data.get("after", {})
            
            # 检查是否是重要字段更新
            important_fields = ["email", "status", "role"]
            changed_fields = []
            
            for field in important_fields:
                if before_data.get(field) != after_data.get(field):
                    changed_fields.append(field)
            
            if changed_fields:
                parameters = {
                    "operation": "sync_user_data",
                    "user_id": after_data.get("id"),
                    "changed_fields": changed_fields,
                    "before": before_data,
                    "after": after_data
                }
                
                self.trigger_plugin("data_processor", parameters, priority="high")
    
    def _handle_order_change(self, event: ChangeEvent):
        """处理订单表变更"""
        if event.event_type == "INSERT":
            # 新订单创建，触发订单处理插件
            order_data = event.data
            parameters = {
                "operation": "process_new_order",
                "order_id": order_data.get("id"),
                "user_id": order_data.get("user_id"),
                "amount": order_data.get("amount"),
                "status": order_data.get("status")
            }
            
            self.trigger_plugin("order_processor", parameters, priority="high")
    
    def on_error(self, event: ChangeEvent, error: Exception):
        """自定义错误处理"""
        logger.error(f"ExampleConsumer error processing {event.database}.{event.table}: {error}")
        
        # 对于重要的表，可以触发错误处理插件
        if event.table in ["users", "orders"]:
            try:
                parameters = {
                    "operation": "handle_processing_error",
                    "error_type": "consumer_error",
                    "event": event.to_dict(),
                    "error_message": str(error)
                }
                
                self.trigger_plugin("error_handler", parameters, priority="high")
            except Exception as e:
                logger.error(f"Failed to trigger error handler: {e}") 