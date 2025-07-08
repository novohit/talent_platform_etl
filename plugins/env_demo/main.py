"""
环境变量配置演示插件
展示多级环境变量配置的使用方法
"""

import os
import time
from typing import Dict, Any

def demo_env_config(**kwargs) -> Dict[str, Any]:
    """
    演示多级环境变量配置的使用
    
    优先级：插件级 .env > 全局 plugins/.env > 系统环境变量
    """
    print("=" * 60)
    print("环境变量配置演示")
    print("=" * 60)
    
    # 1. 展示全局配置项
    print("\n1. 全局配置项（来自 plugins/.env）:")
    global_vars = [
        "API_BASE_URL", "API_VERSION", "API_TIMEOUT",
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER",
        "LOG_LEVEL", "BATCH_SIZE", "SYSTEM_ENV"
    ]
    
    for var in global_vars:
        value = os.getenv(var, "未设置")
        print(f"   {var} = {value}")
    
    # 2. 展示插件特定配置项
    print("\n2. 插件特定配置项（来自 plugins/env_demo/.env）:")
    plugin_vars = [
        "PLUGIN_NAME", "PLUGIN_VERSION", "DEMO_MESSAGE",
        "DEMO_ENABLED", "DEMO_MAX_ITERATIONS", "DEMO_API_KEY",
        "TEMP_PREFIX", "CACHE_TTL"
    ]
    
    for var in plugin_vars:
        value = os.getenv(var, "未设置")
        print(f"   {var} = {value}")
    
    # 3. 展示覆盖效果
    print("\n3. 配置覆盖效果演示:")
    print("   这些配置项在插件级配置中覆盖了全局配置:")
    
    override_demo = {
        "API_BASE_URL": {
            "global": "https://api.example.com",
            "plugin": os.getenv("API_BASE_URL", "未设置")
        },
        "LOG_LEVEL": {
            "global": "INFO", 
            "plugin": os.getenv("LOG_LEVEL", "未设置")
        },
        "BATCH_SIZE": {
            "global": "100",
            "plugin": os.getenv("BATCH_SIZE", "未设置")
        }
    }
    
    for var, values in override_demo.items():
        print(f"   {var}:")
        print(f"     全局配置: {values['global']}")
        print(f"     插件配置: {values['plugin']} ({'✓ 已覆盖' if values['plugin'] != '未设置' else '✗ 使用全局'})")
    
    # 4. 实际使用示例
    print("\n4. 配置实际使用示例:")
    
    # 使用合并后的配置
    api_url = os.getenv("API_BASE_URL", "https://api.example.com")
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    demo_enabled = os.getenv("DEMO_ENABLED", "false").lower() == "true"
    max_iterations = int(os.getenv("DEMO_MAX_ITERATIONS", "5"))
    
    print(f"   API基础URL: {api_url}")
    print(f"   批处理大小: {batch_size}")
    print(f"   演示模式: {'启用' if demo_enabled else '禁用'}")
    
    if demo_enabled:
        print(f"\n5. 执行演示任务 (最大 {max_iterations} 次迭代):")
        for i in range(min(max_iterations, 3)):  # 限制演示次数
            print(f"   第 {i+1} 次迭代: 处理 {batch_size} 条记录...")
            time.sleep(0.5)  # 模拟处理时间
        
        if max_iterations > 3:
            print(f"   ... 还有 {max_iterations - 3} 次迭代（演示中省略）")
    
    # 5. 配置验证
    print("\n6. 配置验证:")
    validation_results = []
    
    # 检查必需的配置
    required_configs = ["PLUGIN_NAME", "API_BASE_URL", "DB_HOST"]
    for config in required_configs:
        value = os.getenv(config)
        if value:
            validation_results.append(f"✓ {config}: 已配置")
        else:
            validation_results.append(f"✗ {config}: 缺失")
    
    for result in validation_results:
        print(f"   {result}")
    
    # 返回结果
    result = {
        "status": "success",
        "plugin_name": os.getenv("PLUGIN_NAME", "env_demo"),
        "config_source": "multi-level",
        "global_vars_loaded": len([v for v in global_vars if os.getenv(v)]),
        "plugin_vars_loaded": len([v for v in plugin_vars if os.getenv(v)]),
        "demo_enabled": demo_enabled,
        "iterations_completed": min(max_iterations, 3) if demo_enabled else 0,
        "api_endpoint": api_url,
        "batch_size": batch_size,
        "message": os.getenv("DEMO_MESSAGE", "环境变量演示完成！")
    }
    
    print(f"\n演示完成！插件返回: {result['message']}")
    return result


# 兼容性别名
process_data = demo_env_config 