"""
数据管道插件装饰器
提供各种通用的装饰器功能
"""

import time
import functools
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime

from .logger import get_logger
from .helpers import format_duration


def timing(func: Callable = None, *, logger_name: str = "timing") -> Callable:
    """
    计时装饰器，记录函数执行时间
    
    Args:
        func: 被装饰的函数
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            start_time = time.time()
            logger.debug(f"Starting {f.__name__}")
            
            try:
                result = f(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                
                logger.info(f"{f.__name__} completed in {format_duration(duration)}")
                return result
            
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                logger.error(f"{f.__name__} failed after {format_duration(duration)}: {str(e)}")
                raise
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def error_handler(
    func: Callable = None, 
    *, 
    exceptions: tuple = (Exception,),
    logger_name: str = "error_handler",
    reraise: bool = True,
    default_return: Any = None
) -> Callable:
    """
    错误处理装饰器
    
    Args:
        func: 被装饰的函数
        exceptions: 要捕获的异常类型
        logger_name: 日志器名称
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            try:
                return f(*args, **kwargs)
            except exceptions as e:
                logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
                
                if reraise:
                    raise
                else:
                    return default_return
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def validate_params(
    func: Callable = None,
    *,
    required_params: List[str] = None,
    param_types: Dict[str, type] = None,
    logger_name: str = "validator"
) -> Callable:
    """
    参数验证装饰器
    
    Args:
        func: 被装饰的函数
        required_params: 必需参数列表
        param_types: 参数类型字典
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            # 验证必需参数
            if required_params:
                missing_params = [param for param in required_params if param not in kwargs]
                if missing_params:
                    error_msg = f"{f.__name__} missing required parameters: {missing_params}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # 验证参数类型
            if param_types:
                for param, expected_type in param_types.items():
                    if param in kwargs:
                        actual_value = kwargs[param]
                        if not isinstance(actual_value, expected_type):
                            error_msg = (
                                f"{f.__name__} parameter '{param}' must be {expected_type.__name__}, "
                                f"got {type(actual_value).__name__}"
                            )
                            logger.error(error_msg)
                            raise TypeError(error_msg)
            
            logger.debug(f"{f.__name__} parameter validation passed")
            return f(*args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def cache_result(
    func: Callable = None,
    *,
    ttl: int = 3600,
    max_size: int = 128,
    logger_name: str = "cache"
) -> Callable:
    """
    结果缓存装饰器（简单实现）
    
    Args:
        func: 被装饰的函数
        ttl: 缓存生存时间（秒）
        max_size: 最大缓存大小
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            # 生成缓存键
            cache_key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # 检查缓存
            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]
                if current_time - cached_time < ttl:
                    logger.debug(f"Cache hit for {f.__name__}")
                    return cached_result
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
            
            # 清理过期缓存
            expired_keys = [
                key for key, (_, cached_time) in cache.items()
                if current_time - cached_time >= ttl
            ]
            for key in expired_keys:
                del cache[key]
            
            # 限制缓存大小
            if len(cache) >= max_size:
                # 删除最旧的条目
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            logger.debug(f"Cached result for {f.__name__}")
            return result
        
        # 添加缓存清理方法
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'max_size': max_size,
            'ttl': ttl
        }
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_execution(
    func: Callable = None,
    *,
    log_args: bool = True,
    log_result: bool = False,
    log_level: str = "INFO",
    logger_name: str = "execution"
) -> Callable:
    """
    执行日志装饰器
    
    Args:
        func: 被装饰的函数
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_level: 日志级别
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            log_func = getattr(logger, log_level.lower())
            
            # 记录函数开始执行
            log_msg = f"Executing {f.__name__}"
            if log_args:
                args_str = ', '.join([str(arg) for arg in args])
                kwargs_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
                params_str = ', '.join(filter(None, [args_str, kwargs_str]))
                if params_str:
                    log_msg += f" with parameters: {params_str}"
            
            log_func(log_msg)
            
            try:
                result = f(*args, **kwargs)
                
                # 记录执行成功
                success_msg = f"{f.__name__} executed successfully"
                if log_result and result is not None:
                    success_msg += f", result: {result}"
                
                log_func(success_msg)
                return result
                
            except Exception as e:
                logger.error(f"{f.__name__} execution failed: {str(e)}")
                raise
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def retry(
    func: Callable = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_name: str = "retry"
) -> Callable:
    """
    重试装饰器
    
    Args:
        func: 被装饰的函数
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.info(f"Retrying {f.__name__} (attempt {attempt + 1}/{max_attempts})")
                    
                    return f(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{f.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"{f.__name__} failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
            
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def rate_limit(
    func: Callable = None,
    *,
    calls_per_second: float = 1.0,
    logger_name: str = "rate_limit"
) -> Callable:
    """
    速率限制装饰器
    
    Args:
        func: 被装饰的函数
        calls_per_second: 每秒允许的调用次数
        logger_name: 日志器名称
    
    Returns:
        装饰后的函数
    """
    def decorator(f: Callable) -> Callable:
        min_interval = 1.0 / calls_per_second
        last_called = [0.0]
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            current_time = time.time()
            elapsed = current_time - last_called[0]
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"Rate limiting {f.__name__}, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            last_called[0] = time.time()
            return f(*args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func) 