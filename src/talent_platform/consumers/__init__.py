"""
Canal数据库变更消费者模块
"""

from .consumer_manager import consumer_manager
from .base_consumer import BaseConsumer

__all__ = ['consumer_manager', 'BaseConsumer'] 