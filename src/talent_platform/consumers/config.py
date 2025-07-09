"""
Canal消费者配置
"""

import os
from typing import Dict, Any


class CanalConfig:
    """Canal连接配置"""
    
    # Canal服务器配置
    CANAL_HOST = os.getenv('CANAL_HOST', '127.0.0.1')
    CANAL_PORT = int(os.getenv('CANAL_PORT', '11111'))
    CANAL_DESTINATION = os.getenv('CANAL_DESTINATION', 'example')
    CANAL_USERNAME = os.getenv('CANAL_USERNAME', '')
    CANAL_PASSWORD = os.getenv('CANAL_PASSWORD', '')
    
    # 消费配置
    CANAL_BATCH_SIZE = int(os.getenv('CANAL_BATCH_SIZE', '100'))
    CANAL_TIMEOUT = int(os.getenv('CANAL_TIMEOUT', '1'))
    
    # 自动重连配置
    AUTO_RECONNECT = os.getenv('AUTO_RECONNECT', 'true').lower() == 'true'
    RECONNECT_INTERVAL = int(os.getenv('RECONNECT_INTERVAL', '30'))  # 秒
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', '10'))
    
    @classmethod
    def get_canal_config(cls) -> Dict[str, Any]:
        """获取Canal配置字典"""
        return {
            'host': cls.CANAL_HOST,
            'port': cls.CANAL_PORT,
            'destination': cls.CANAL_DESTINATION,
            'username': cls.CANAL_USERNAME,
            'password': cls.CANAL_PASSWORD,
            'batch_size': cls.CANAL_BATCH_SIZE,
            'timeout': cls.CANAL_TIMEOUT
        }
    
    @classmethod
    def get_reconnect_config(cls) -> Dict[str, Any]:
        """获取重连配置"""
        return {
            'auto_reconnect': cls.AUTO_RECONNECT,
            'reconnect_interval': cls.RECONNECT_INTERVAL,
            'max_attempts': cls.MAX_RECONNECT_ATTEMPTS
        } 