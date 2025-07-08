"""
热加载功能演示插件
用于演示插件的热加载和更新机制，以及插件级环境变量的使用
支持代码热加载和环境变量热加载
"""

import os
import logging
import time
import random
from datetime import datetime
from typing import Dict, Any


# 配置日志
logger = logging.getLogger(__name__)


def test_env_hot_reload(**kwargs) -> Dict[str, Any]:
    """
    专门用于测试环境变量热加载的函数
    
    🔥 环境变量热加载测试：
    1. 修改 plugins/hot_reload_demo/.env 文件
    2. 保存文件后会自动触发插件重新加载
    3. 下次执行会使用新的环境变量值
    """
    
    print("=" * 80)
    print("🔥 环境变量热加载测试")
    print("=" * 80)
    
    # 从环境变量读取配置
    test_message = os.getenv('HOT_RELOAD_TEST_MESSAGE', '默认测试消息')
    test_count = int(os.getenv('TEST_ITERATION_COUNT', '3'))
    test_delay = float(os.getenv('TEST_DELAY_SECONDS', '1.0'))
    enable_debug = os.getenv('ENABLE_DEBUG_OUTPUT', 'false').lower() == 'true'
    color_theme = os.getenv('OUTPUT_COLOR_THEME', 'blue')
    
    # 显示当前配置
    print(f"📋 当前环境变量配置：")
    print(f"   HOT_RELOAD_TEST_MESSAGE = '{test_message}'")
    print(f"   TEST_ITERATION_COUNT = {test_count}")
    print(f"   TEST_DELAY_SECONDS = {test_delay}")
    print(f"   ENABLE_DEBUG_OUTPUT = {enable_debug}")
    print(f"   OUTPUT_COLOR_THEME = {color_theme}")
    
    # 显示全局配置覆盖情况
    print(f"\n🌍 全局配置继承情况：")
    global_configs = {
        "API_BASE_URL": os.getenv("API_BASE_URL", "未设置"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "未设置"),
        "BATCH_SIZE": os.getenv("BATCH_SIZE", "未设置"),
        "SYSTEM_ENV": os.getenv("SYSTEM_ENV", "未设置")
    }
    
    for key, value in global_configs.items():
        source = "插件级覆盖" if "hot-reload" in str(value).lower() else "全局/系统配置"
        print(f"   {key} = {value} ({source})")
    
    # 执行测试迭代
    results = []
    
    print(f"\n🚀 开始执行 {test_count} 次测试迭代...")
    
    for i in range(test_count):
        start_time = time.time()
        
        # 根据颜色主题选择图标
        icons = {
            'blue': '🔵',
            'green': '🟢', 
            'red': '🔴',
            'yellow': '🟡',
            'purple': '🟣'
        }
        icon = icons.get(color_theme, '⚪')
        
        # 模拟一些处理
        processing_time = random.uniform(0.1, test_delay)
        time.sleep(processing_time)
        
        iteration_result = {
            "iteration": i + 1,
            "message": f"{test_message} - 第{i+1}次",
            "processing_time": round(processing_time, 2),
            "random_value": random.randint(1, 1000),
            "timestamp": datetime.now().isoformat(),
            "color_theme": color_theme
        }
        
        results.append(iteration_result)
        
        print(f"   {icon} 第 {i+1} 次: {iteration_result['message']} "
              f"(用时: {processing_time:.2f}s, 随机值: {iteration_result['random_value']})")
        
        if enable_debug:
            print(f"      🐛 DEBUG: 迭代详情 = {iteration_result}")
    
    print(f"\n✅ 测试完成！共执行 {len(results)} 次迭代")
    
    # 显示修改提示
    print(f"\n💡 环境变量热加载测试指南：")
    print(f"   1. 修改 plugins/hot_reload_demo/.env 文件中的值：")
    print(f"      HOT_RELOAD_TEST_MESSAGE=\"新的测试消息\"")
    print(f"      TEST_ITERATION_COUNT=5")
    print(f"      OUTPUT_COLOR_THEME=green")
    print(f"      ENABLE_DEBUG_OUTPUT=true")
    print(f"   ")
    print(f"   2. 保存 .env 文件后，系统会自动检测到变化并重新加载插件")
    print(f"   ")
    print(f"   3. 重新运行此测试查看新配置生效：")
    print(f"      python -m talent_platform.scheduler_app test-plugin hot_reload_demo --operation test_env_hot_reload")
    
    # 返回结果
    return {
        "status": "success",
        "test_type": "env_hot_reload",
        "environment_config": {
            "test_message": test_message,
            "test_count": test_count,
            "test_delay": test_delay,
            "enable_debug": enable_debug,
            "color_theme": color_theme
        },
        "global_config": global_configs,
        "iterations": results,
        "total_iterations": len(results),
        "avg_processing_time": round(sum(r["processing_time"] for r in results) / len(results), 2),
        "timestamp": datetime.now().isoformat(),
        "hot_reload_info": {
            "supports_env_reload": True,
            "env_file_path": "plugins/hot_reload_demo/.env",
            "last_test": datetime.now().isoformat()
        }
    }


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