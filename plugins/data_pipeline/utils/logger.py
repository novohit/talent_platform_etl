"""
数据管道插件日志工具
提供统一的日志配置和管理功能
"""

import os
import sys
import logging
from typing import Optional
from datetime import datetime


class PluginLogger:
    """插件专用日志器"""
    
    def __init__(self, name: str, level: str = None):
        self.name = name
        self.level = level or os.getenv('LOG_LEVEL', 'INFO')
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger(f"data_pipeline.{self.name}")
        logger.setLevel(getattr(logging, self.level.upper()))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了日志目录）
        log_dir = os.getenv('LOG_DIR')
        if log_dir and os.path.exists(log_dir):
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f'data_pipeline_{self.name}.log')
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, msg: str, **kwargs):
        """调试级别日志"""
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        """信息级别日志"""
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """警告级别日志"""
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        """错误级别日志"""
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        """严重错误级别日志"""
        self.logger.critical(msg, **kwargs)
    
    def log_operation(self, operation: str, status: str, details: dict = None):
        """记录操作日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'details': details or {}
        }
        
        if status == 'success':
            self.info(f"Operation {operation} completed successfully", extra=log_entry)
        elif status == 'error':
            self.error(f"Operation {operation} failed", extra=log_entry)
        else:
            self.info(f"Operation {operation} status: {status}", extra=log_entry)


def get_logger(name: str, level: str = None) -> PluginLogger:
    """
    获取插件日志器
    
    Args:
        name: 日志器名称
        level: 日志级别（可选）
    
    Returns:
        PluginLogger实例
    """
    return PluginLogger(name, level)


def setup_logging(plugin_name: str = "data_pipeline"):
    """
    设置插件日志配置
    
    Args:
        plugin_name: 插件名称
    """
    # 从环境变量读取配置
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'standard')
    
    # 配置根日志器
    root_logger = logging.getLogger(plugin_name)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置格式
    if log_format == 'json':
        import json
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                return json.dumps(log_record)
        
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger 