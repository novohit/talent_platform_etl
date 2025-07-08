"""
数据管道插件配置管理
提供配置加载、验证和管理功能
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..utils.helpers import (
    parse_env_int, parse_env_float, parse_env_bool, 
    parse_env_list, validate_config
)


@dataclass
class FetcherConfig:
    """数据获取器配置"""
    # API配置
    api_base_url: str = field(default_factory=lambda: os.getenv('API_BASE_URL', 'https://api.example.com'))
    api_timeout: int = field(default_factory=lambda: parse_env_int('API_TIMEOUT', 30))
    api_retries: int = field(default_factory=lambda: parse_env_int('API_RETRIES', 3))
    api_rate_limit: float = field(default_factory=lambda: parse_env_float('API_RATE_LIMIT', 1.0))
    
    # 数据库配置
    db_host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    db_port: int = field(default_factory=lambda: parse_env_int('DB_PORT', 5432))
    db_name: str = field(default_factory=lambda: os.getenv('DB_NAME', 'talent_platform'))
    db_user: str = field(default_factory=lambda: os.getenv('DB_USER', 'user'))
    db_password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    
    # 文件配置
    file_input_dir: str = field(default_factory=lambda: os.getenv('FILE_INPUT_DIR', '/data/input'))
    file_supported_formats: List[str] = field(default_factory=lambda: parse_env_list('FILE_FORMATS', default=['json', 'csv', 'xlsx']))


@dataclass
class ProcessorConfig:
    """数据处理器配置"""
    # 处理配置
    batch_size: int = field(default_factory=lambda: parse_env_int('BATCH_SIZE', 100))
    max_workers: int = field(default_factory=lambda: parse_env_int('MAX_WORKERS', 4))
    chunk_size: int = field(default_factory=lambda: parse_env_int('CHUNK_SIZE', 1000))
    
    # 验证配置
    strict_validation: bool = field(default_factory=lambda: parse_env_bool('STRICT_VALIDATION', True))
    validation_rules: List[str] = field(default_factory=lambda: parse_env_list('VALIDATION_RULES'))
    
    # 清洗配置
    remove_duplicates: bool = field(default_factory=lambda: parse_env_bool('REMOVE_DUPLICATES', True))
    normalize_text: bool = field(default_factory=lambda: parse_env_bool('NORMALIZE_TEXT', True))
    handle_missing_values: str = field(default_factory=lambda: os.getenv('HANDLE_MISSING_VALUES', 'skip'))
    
    # 转换配置
    date_format: str = field(default_factory=lambda: os.getenv('DATE_FORMAT', '%Y-%m-%d'))
    encoding: str = field(default_factory=lambda: os.getenv('TEXT_ENCODING', 'utf-8'))


@dataclass
class StorageConfig:
    """数据存储器配置"""
    # 数据库存储
    storage_db_host: str = field(default_factory=lambda: os.getenv('STORAGE_DB_HOST', 'localhost'))
    storage_db_port: int = field(default_factory=lambda: parse_env_int('STORAGE_DB_PORT', 5432))
    storage_db_name: str = field(default_factory=lambda: os.getenv('STORAGE_DB_NAME', 'talent_platform'))
    storage_table_prefix: str = field(default_factory=lambda: os.getenv('STORAGE_TABLE_PREFIX', 'pipeline_'))
    
    # 文件存储
    file_output_dir: str = field(default_factory=lambda: os.getenv('FILE_OUTPUT_DIR', '/data/output'))
    file_backup_dir: str = field(default_factory=lambda: os.getenv('FILE_BACKUP_DIR', '/data/backup'))
    file_retention_days: int = field(default_factory=lambda: parse_env_int('FILE_RETENTION_DAYS', 30))
    
    # 缓存配置
    cache_enabled: bool = field(default_factory=lambda: parse_env_bool('CACHE_ENABLED', True))
    cache_ttl: int = field(default_factory=lambda: parse_env_int('CACHE_TTL', 3600))
    cache_max_size: int = field(default_factory=lambda: parse_env_int('CACHE_MAX_SIZE', 1000))
    
    # Redis配置
    redis_host: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    redis_port: int = field(default_factory=lambda: parse_env_int('REDIS_PORT', 6379))
    redis_db: int = field(default_factory=lambda: parse_env_int('REDIS_DB', 0))


@dataclass
class PipelineConfig:
    """管道配置"""
    # 管道流程
    pipeline_name: str = field(default_factory=lambda: os.getenv('PIPELINE_NAME', 'data_pipeline'))
    pipeline_version: str = field(default_factory=lambda: os.getenv('PIPELINE_VERSION', '1.0.0'))
    pipeline_description: str = field(default_factory=lambda: os.getenv('PIPELINE_DESC', 'Data processing pipeline'))
    
    # 执行配置
    execution_mode: str = field(default_factory=lambda: os.getenv('EXECUTION_MODE', 'sequential'))  # sequential, parallel
    dry_run: bool = field(default_factory=lambda: parse_env_bool('DRY_RUN', False))
    continue_on_error: bool = field(default_factory=lambda: parse_env_bool('CONTINUE_ON_ERROR', False))
    
    # 监控配置
    enable_metrics: bool = field(default_factory=lambda: parse_env_bool('ENABLE_METRICS', True))
    metrics_interval: int = field(default_factory=lambda: parse_env_int('METRICS_INTERVAL', 60))
    
    # 日志配置
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 'standard'))
    log_to_file: bool = field(default_factory=lambda: parse_env_bool('LOG_TO_FILE', False))


@dataclass
class DataPipelineConfig:
    """数据管道完整配置"""
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    processor: ProcessorConfig = field(default_factory=ProcessorConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    
    # 全局配置
    plugin_name: str = field(default_factory=lambda: os.getenv('PLUGIN_NAME', 'data_pipeline'))
    debug_mode: bool = field(default_factory=lambda: parse_env_bool('DEBUG_MODE', False))
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'fetcher': self.fetcher.__dict__,
            'processor': self.processor.__dict__,
            'storage': self.storage.__dict__,
            'pipeline': self.pipeline.__dict__,
            'global': {
                'plugin_name': self.plugin_name,
                'debug_mode': self.debug_mode,
                'environment': self.environment
            }
        }
    
    def get_required_env_vars(self) -> List[str]:
        """获取必需的环境变量列表"""
        return [
            'DB_HOST', 'DB_NAME', 'DB_USER',  # 数据库必需
            'FILE_INPUT_DIR', 'FILE_OUTPUT_DIR',  # 文件目录必需
        ]
    
    def validate(self) -> Dict[str, Any]:
        """验证配置的完整性"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'missing_optional': []
        }
        
        # 验证必需的环境变量
        required_vars = self.get_required_env_vars()
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Missing required environment variables: {missing_vars}")
        
        # 验证目录路径
        directories = [
            self.fetcher.file_input_dir,
            self.storage.file_output_dir,
            self.storage.file_backup_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                validation_results['warnings'].append(f"Directory does not exist: {directory}")
        
        # 验证数据库连接信息
        if not self.fetcher.db_password:
            validation_results['warnings'].append("Database password is empty")
        
        # 验证批次大小
        if self.processor.batch_size <= 0:
            validation_results['errors'].append("Batch size must be positive")
            validation_results['valid'] = False
        
        # 验证执行模式
        valid_modes = ['sequential', 'parallel']
        if self.pipeline.execution_mode not in valid_modes:
            validation_results['errors'].append(f"Invalid execution mode: {self.pipeline.execution_mode}")
            validation_results['valid'] = False
        
        return validation_results


# 全局配置实例
_config_instance: Optional[DataPipelineConfig] = None


def get_config(reload: bool = False) -> DataPipelineConfig:
    """
    获取全局配置实例（单例模式）
    
    Args:
        reload: 是否重新加载配置
    
    Returns:
        DataPipelineConfig实例
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = DataPipelineConfig()
    
    return _config_instance


def load_config_from_env() -> DataPipelineConfig:
    """
    从环境变量加载配置
    
    Returns:
        新的DataPipelineConfig实例
    """
    return DataPipelineConfig()


def validate_configuration() -> Dict[str, Any]:
    """
    验证当前配置
    
    Returns:
        验证结果字典
    """
    config = get_config()
    return config.validate()


def get_config_summary() -> Dict[str, Any]:
    """
    获取配置摘要信息
    
    Returns:
        配置摘要字典
    """
    config = get_config()
    
    return {
        'plugin_info': {
            'name': config.plugin_name,
            'environment': config.environment,
            'debug_mode': config.debug_mode,
            'pipeline_version': config.pipeline.pipeline_version
        },
        'fetcher_info': {
            'api_base_url': config.fetcher.api_base_url,
            'db_host': config.fetcher.db_host,
            'supported_formats': config.fetcher.file_supported_formats
        },
        'processor_info': {
            'batch_size': config.processor.batch_size,
            'max_workers': config.processor.max_workers,
            'strict_validation': config.processor.strict_validation
        },
        'storage_info': {
            'db_host': config.storage.storage_db_host,
            'cache_enabled': config.storage.cache_enabled,
            'retention_days': config.storage.file_retention_days
        },
        'pipeline_info': {
            'execution_mode': config.pipeline.execution_mode,
            'dry_run': config.pipeline.dry_run,
            'metrics_enabled': config.pipeline.enable_metrics
        }
    }


def update_config(**kwargs) -> DataPipelineConfig:
    """
    更新配置（主要用于测试）
    
    Args:
        **kwargs: 要更新的配置项
    
    Returns:
        更新后的配置实例
    """
    config = get_config()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config 