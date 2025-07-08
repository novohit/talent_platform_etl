"""
热加载功能演示插件
用于演示插件的热加载和更新机制，以及插件级环境变量的使用
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any


# 配置日志
logger = logging.getLogger(__name__)


def demo_function(message: str = "Hello from hot reload demo!", 
                 count: int = 1,
                 **kwargs) -> Dict[str, Any]:
    """
    演示函数 - 版本 1.0
    
    Args:
        message: 演示消息
        count: 重复次数
        **kwargs: 其他参数
    
    Returns:
        处理结果字典
    """
    
    # 从环境变量中读取配置
    plugin_name = os.getenv('PLUGIN_NAME', 'hot_reload_demo')
    plugin_version = os.getenv('PLUGIN_VERSION', '1.0')
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    max_retry = int(os.getenv('MAX_RETRY_COUNT', '3'))
    message_prefix = os.getenv('DEFAULT_MESSAGE_PREFIX', '[DEMO]')
    api_timeout = int(os.getenv('API_TIMEOUT', '30'))
    external_api_url = os.getenv('EXTERNAL_API_URL', 'https://api.example.com')
    demo_enabled = os.getenv('DEMO_ENABLED', 'true').lower() == 'true'
    batch_size = int(os.getenv('DEMO_BATCH_SIZE', '100'))
    
    logger.info(f"Hot reload demo v{plugin_version} - Processing: message='{message}', count={count}")
    
    if debug_mode:
        logger.info(f"Debug mode enabled - Plugin: {plugin_name}")
        logger.info(f"Configuration: max_retry={max_retry}, timeout={api_timeout}, batch_size={batch_size}")
        logger.info(f"External API: {external_api_url}")
    
    if not demo_enabled:
        logger.warning("Demo is disabled by environment configuration")
        return {
            "status": "disabled",
            "message": "Plugin is disabled by DEMO_ENABLED environment variable"
        }
    
    # 生成结果
    results = []
    for i in range(min(count, batch_size)):  # 使用环境变量限制批次大小
        result_message = f"{message_prefix} [{i+1}] {message}"
        results.append(result_message)
        if debug_mode:
            logger.debug(f"Generated: {result_message}")
    
    # 模拟一些处理时间
    import time
    time.sleep(0.1)
    
    # 返回结果，包含环境配置信息
    response = {
        "status": "success",
        "operation": "demo_function",
        "version": plugin_version,
        "plugin_info": {
            "name": plugin_name,
            "version": plugin_version,
            "description": "这是第一个版本的演示插件，支持环境变量配置",
            "debug_mode": debug_mode,
            "environment_config": {
                "max_retry_count": max_retry,
                "api_timeout": api_timeout,
                "batch_size": batch_size,
                "external_api_url": external_api_url,
                "demo_enabled": demo_enabled
            }
        },
        "result": {
            "input_message": message,
            "input_count": count,
            "actual_processed": len(results),
            "generated_messages": results,
            "total_messages": len(results),
            "processing_time": "~0.1s",
            "message_prefix": message_prefix
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Hot reload demo completed successfully - generated {len(results)} messages")
    
    if debug_mode:
        logger.debug(f"Full response: {response}")
    
    return response 