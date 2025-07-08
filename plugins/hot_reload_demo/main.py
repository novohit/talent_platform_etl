"""
热加载功能演示插件
用于演示插件的热加载和更新机制
"""

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
    
    logger.info(f"Hot reload demo v1.0 - Processing: message='{message}', count={count}")
    
    # 生成结果
    results = []
    for i in range(count):
        result_message = f"[{i+1}] {message}"
        results.append(result_message)
        logger.info(f"Generated: {result_message}")
    
    # 模拟一些处理时间
    import time
    time.sleep(0.1)
    
    # 返回结果
    response = {
        "status": "success",
        "operation": "demo_function",
        "version": "1.0",
        "plugin_info": {
            "name": "hot_reload_demo",
            "version": "1.0",
            "description": "这是第一个版本的演示插件"
        },
        "result": {
            "input_message": message,
            "input_count": count,
            "generated_messages": results,
            "total_messages": len(results),
            "processing_time": "~0.1s"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Hot reload demo completed successfully - generated {len(results)} messages")
    
    return response 