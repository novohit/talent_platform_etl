"""
数据管道插件辅助函数
提供各种通用的辅助功能和工具函数
"""

import os
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析JSON字符串
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
    
    Returns:
        解析后的对象或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全地序列化对象为JSON
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
    
    Returns:
        JSON字符串或默认值
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except (TypeError, ValueError):
        return default


def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    失败重试装饰器函数
    
    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
    
    Returns:
        函数执行结果
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                raise e
            
            wait_time = delay * (backoff_factor ** attempt)
            time.sleep(wait_time)
            continue


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> Dict[str, Any]:
    """
    验证配置字典
    
    Args:
        config: 配置字典
        required_keys: 必需的配置键列表
    
    Returns:
        验证结果字典
    
    Raises:
        ValueError: 当缺少必需配置时
    """
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {missing_keys}")
    
    return {
        'valid': True,
        'missing_keys': [],
        'present_keys': list(config.keys()),
        'required_keys': required_keys
    }


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
    
    Returns:
        格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    
    while size_bytes >= 1024 and size_index < len(size_names) - 1:
        size_bytes /= 1024.0
        size_index += 1
    
    return f"{size_bytes:.1f} {size_names[size_index]}"


def format_duration(seconds: float) -> str:
    """
    格式化时间持续时间
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256）
    
    Returns:
        文件哈希值
    """
    hash_func = getattr(hashlib, algorithm)()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (IOError, OSError):
        return ""


def ensure_directory(dir_path: str) -> bool:
    """
    确保目录存在，不存在则创建
    
    Args:
        dir_path: 目录路径
    
    Returns:
        是否成功创建或目录已存在
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分割成指定大小的块
    
    Args:
        lst: 要分割的列表
        chunk_size: 块大小
    
    Returns:
        分割后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并两个字典
    
    Args:
        dict1: 基础字典
        dict2: 要合并的字典
    
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def get_timestamp(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间戳
    
    Args:
        format_str: 时间格式字符串
    
    Returns:
        格式化后的时间字符串
    """
    return datetime.now().strftime(format_str)


def parse_env_int(key: str, default: int = 0) -> int:
    """
    安全解析环境变量为整数
    
    Args:
        key: 环境变量键
        default: 默认值
    
    Returns:
        整数值
    """
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def parse_env_float(key: str, default: float = 0.0) -> float:
    """
    安全解析环境变量为浮点数
    
    Args:
        key: 环境变量键
        default: 默认值
    
    Returns:
        浮点数值
    """
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def parse_env_bool(key: str, default: bool = False) -> bool:
    """
    安全解析环境变量为布尔值
    
    Args:
        key: 环境变量键
        default: 默认值
    
    Returns:
        布尔值
    """
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on', 'enabled')


def parse_env_list(key: str, separator: str = ',', default: List[str] = None) -> List[str]:
    """
    安全解析环境变量为列表
    
    Args:
        key: 环境变量键
        separator: 分隔符
        default: 默认值
    
    Returns:
        字符串列表
    """
    if default is None:
        default = []
    
    value = os.getenv(key)
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]


class Timer:
    """计时器上下文管理器"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        """获取执行时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def elapsed_str(self) -> str:
        """获取格式化的执行时间"""
        return format_duration(self.elapsed) 