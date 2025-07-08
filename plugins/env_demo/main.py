"""
环境变量配置演示插件
展示如何在插件中使用各种类型的环境变量配置
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


def parse_env_bool(value: str, default: bool = False) -> bool:
    """解析环境变量布尔值"""
    if not value:
        return default
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')


def parse_env_int(value: str, default: int = 0) -> int:
    """解析环境变量整数值"""
    try:
        return int(value) if value else default
    except ValueError:
        logger.warning(f"Invalid integer value in environment: {value}, using default: {default}")
        return default


def parse_env_float(value: str, default: float = 0.0) -> float:
    """解析环境变量浮点数值"""
    try:
        return float(value) if value else default
    except ValueError:
        logger.warning(f"Invalid float value in environment: {value}, using default: {default}")
        return default


def parse_env_list(value: str, separator: str = ',', default: list = None) -> list:
    """解析环境变量列表值"""
    if not value:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


def parse_env_json(value: str, default: dict = None) -> dict:
    """解析环境变量JSON值"""
    if not value:
        return default or {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in environment: {value}, error: {e}, using default")
        return default or {}


class EnvironmentConfig:
    """环境配置管理类"""
    
    def __init__(self):
        # 基础配置
        self.plugin_name = os.getenv('PLUGIN_NAME', 'env_demo')
        self.debug = parse_env_bool(os.getenv('DEBUG', 'false'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # 业务配置
        self.max_items = parse_env_int(os.getenv('MAX_ITEMS', '1000'))
        self.timeout = parse_env_float(os.getenv('TIMEOUT', '30.0'))
        self.retry_count = parse_env_int(os.getenv('RETRY_COUNT', '3'))
        self.batch_size = parse_env_int(os.getenv('BATCH_SIZE', '100'))
        
        # 功能开关
        self.features_enabled = parse_env_list(os.getenv('FEATURES_ENABLED', 'basic,advanced'))
        self.cache_enabled = parse_env_bool(os.getenv('CACHE_ENABLED', 'true'))
        self.monitoring_enabled = parse_env_bool(os.getenv('MONITORING_ENABLED', 'true'))
        
        # 外部服务配置
        self.api_base_url = os.getenv('API_BASE_URL', 'https://api.example.com')
        self.api_key = os.getenv('API_KEY', 'default_key')
        self.api_version = os.getenv('API_VERSION', 'v1')
        
        # 数据库配置
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = parse_env_int(os.getenv('DB_PORT', '3306'))
        self.db_name = os.getenv('DB_NAME', 'default_db')
        self.db_user = os.getenv('DB_USER', 'user')
        self.db_password = os.getenv('DB_PASSWORD', 'password')
        
        # 高级配置（JSON格式）
        self.custom_settings = parse_env_json(os.getenv('CUSTOM_SETTINGS', '{}'))
        self.mapping_rules = parse_env_json(os.getenv('MAPPING_RULES', '{}'))
        
        # 文件路径配置
        self.data_dir = os.getenv('DATA_DIR', '/tmp/plugin_data')
        self.log_dir = os.getenv('LOG_DIR', '/tmp/logs')
        self.backup_dir = os.getenv('BACKUP_DIR', '/tmp/backup')
        
        # 安全配置
        self.ssl_verify = parse_env_bool(os.getenv('SSL_VERIFY', 'true'))
        self.encryption_key = os.getenv('ENCRYPTION_KEY', '')
        
        if self.debug:
            logger.info(f"Environment configuration loaded for {self.plugin_name}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'plugin_name': self.plugin_name,
            'debug': self.debug,
            'log_level': self.log_level,
            'max_items': self.max_items,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'batch_size': self.batch_size,
            'features_enabled': self.features_enabled,
            'cache_enabled': self.cache_enabled,
            'monitoring_enabled': self.monitoring_enabled,
            'api_base_url': self.api_base_url,
            'api_version': self.api_version,
            'db_host': self.db_host,
            'db_port': self.db_port,
            'db_name': self.db_name,
            'custom_settings': self.custom_settings,
            'mapping_rules': self.mapping_rules,
            'data_dir': self.data_dir,
            'ssl_verify': self.ssl_verify,
            'has_encryption_key': bool(self.encryption_key)
        }


def process_with_env(operation: str, 
                    data_source: str = "default",
                    override_config: Optional[Dict] = None,
                    **kwargs) -> Dict[str, Any]:
    """
    使用环境变量配置进行处理的演示函数
    
    Args:
        operation: 操作类型
        data_source: 数据源
        override_config: 临时覆盖配置
        **kwargs: 其他参数
    
    Returns:
        处理结果字典
    """
    
    # 加载环境配置
    config = EnvironmentConfig()
    
    # 应用临时覆盖配置
    if override_config:
        logger.info(f"Applying override config: {list(override_config.keys())}")
        for key, value in override_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    logger.info(f"Processing operation '{operation}' with data source '{data_source}'")
    
    if config.debug:
        logger.debug(f"Environment configuration: {config.to_dict()}")
    
    # 模拟业务逻辑
    results = []
    
    # 检查功能开关
    if 'basic' in config.features_enabled:
        results.append(f"Basic processing completed for {data_source}")
    
    if 'advanced' in config.features_enabled:
        results.append(f"Advanced processing with batch size {config.batch_size}")
    
    if config.cache_enabled:
        results.append("Cache optimization applied")
    
    if config.monitoring_enabled:
        results.append("Monitoring metrics collected")
    
    # 模拟数据库连接信息（不包含密码）
    db_info = f"Connected to {config.db_host}:{config.db_port}/{config.db_name}"
    results.append(db_info)
    
    # 模拟API调用
    api_info = f"API endpoint: {config.api_base_url}/{config.api_version}"
    results.append(api_info)
    
    # 使用自定义设置
    if config.custom_settings:
        results.append(f"Applied custom settings: {list(config.custom_settings.keys())}")
    
    # 处理完成
    processing_summary = {
        "operation": operation,
        "data_source": data_source,
        "items_processed": min(len(results), config.max_items),
        "timeout_used": config.timeout,
        "retry_count": config.retry_count,
        "features_used": config.features_enabled,
        "ssl_verified": config.ssl_verify
    }
    
    response = {
        "status": "success",
        "operation": operation,
        "plugin_name": config.plugin_name,
        "timestamp": datetime.now().isoformat(),
        "environment_config": config.to_dict(),
        "processing_summary": processing_summary,
        "results": results,
        "debug_mode": config.debug
    }
    
    logger.info(f"Environment demo completed: processed {len(results)} items")
    
    if config.debug:
        logger.debug(f"Full response: {json.dumps(response, indent=2, default=str)}")
    
    return response 