#!/usr/bin/env python3
"""
插件调试工具
用于调试和测试插件，无需修改插件代码
"""

import sys
import os
import json
import argparse
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from talent_platform.logger import logger


class PluginDebugger:
    """插件调试器"""
    
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.plugin_dir = project_root / "plugins" / plugin_name
        self.logger = logger
        
        if not self.plugin_dir.exists():
            raise ValueError(f"Plugin directory not found: {self.plugin_dir}")
        
        # 添加插件目录到路径，支持绝对导入
        if str(self.plugin_dir.parent) not in sys.path:
            sys.path.insert(0, str(self.plugin_dir.parent))
        
        # 关键：添加插件目录本身到路径，让插件内部的绝对导入能正常工作
        if str(self.plugin_dir) not in sys.path:
            sys.path.insert(0, str(self.plugin_dir))
    
    def load_plugin_info(self) -> Dict[str, Any]:
        """加载插件信息"""
        plugin_json_path = self.plugin_dir / "plugin.json"
        
        if not plugin_json_path.exists():
            raise ValueError(f"Plugin configuration not found: {plugin_json_path}")
        
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_plugin_module(self):
        """加载插件模块"""
        plugin_info = self.load_plugin_info()
        entry_point = plugin_info.get("entry_point", "main")
        
        # 尝试作为包导入
        try:
            spec = importlib.util.spec_from_file_location(
                f"{self.plugin_name}.main",
                self.plugin_dir / "main.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError("Could not create module spec")
            
            module = importlib.util.module_from_spec(spec)
            
            # 添加包上下文，让相对导入工作
            sys.modules[self.plugin_name] = importlib.import_module(self.plugin_name)
            sys.modules[f"{self.plugin_name}.main"] = module
            
            spec.loader.exec_module(module)
            return module
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin as package: {e}")
            raise
    
    def get_entry_function(self, module, function_name: str = None):
        """获取插件入口函数"""
        plugin_info = self.load_plugin_info()
        
        if function_name:
            entry_function = function_name
        else:
            entry_function = plugin_info.get("entry_function", "process_data")
        
        if not hasattr(module, entry_function):
            available_functions = [name for name in dir(module) if not name.startswith('_')]
            raise ValueError(
                f"Entry function '{entry_function}' not found in plugin. "
                f"Available functions: {available_functions}"
            )
        
        return getattr(module, entry_function)
    
    def execute_plugin(self, function_name: str = None, **kwargs) -> Any:
        """执行插件"""
        self.logger.info(f"Loading plugin: {self.plugin_name}")
        
        try:
            # 加载插件模块
            module = self.load_plugin_module()
            
            # 获取入口函数
            entry_function = self.get_entry_function(module, function_name)
            
            self.logger.info(f"Executing function: {entry_function.__name__}")
            self.logger.info(f"Parameters: {kwargs}")
            
            # 执行插件
            result = entry_function(**kwargs)
            
            self.logger.info("Plugin execution completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Plugin execution failed: {e}")
            raise
    
    def list_functions(self) -> list:
        """列出插件中的可用函数"""
        try:
            module = self.load_plugin_module()
            functions = []
            
            for name in dir(module):
                if not name.startswith('_'):
                    obj = getattr(module, name)
                    if callable(obj):
                        functions.append({
                            'name': name,
                            'type': 'function' if hasattr(obj, '__call__') else 'class',
                            'doc': getattr(obj, '__doc__', '').strip() if hasattr(obj, '__doc__') else None
                        })
            
            return functions
            
        except Exception as e:
            self.logger.error(f"Failed to list functions: {e}")
            return []
    
    def show_plugin_info(self):
        """显示插件信息"""
        try:
            plugin_info = self.load_plugin_info()
            functions = self.list_functions()
            
            print(f"\n{'='*60}")
            print(f"插件信息: {self.plugin_name}")
            print(f"{'='*60}")
            print(f"名称: {plugin_info.get('name', 'N/A')}")
            print(f"版本: {plugin_info.get('version', 'N/A')}")
            print(f"描述: {plugin_info.get('description', 'N/A')}")
            print(f"作者: {plugin_info.get('author', 'N/A')}")
            print(f"入口函数: {plugin_info.get('entry_function', 'process_data')}")
            print(f"启用状态: {'✓' if plugin_info.get('enabled', True) else '✗'}")
            
            if plugin_info.get('dependencies'):
                print(f"\n依赖:")
                for dep in plugin_info['dependencies']:
                    print(f"  - {dep}")
            
            if functions:
                print(f"\n可用函数:")
                for func in functions:
                    print(f"  - {func['name']} ({func['type']})")
                    if func['doc']:
                        print(f"    {func['doc']}")
            
            print(f"\n{'='*60}")
            
        except Exception as e:
            self.logger.error(f"Failed to show plugin info: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="插件调试工具")
    parser.add_argument("plugin", help="插件名称")
    parser.add_argument("--info", action="store_true", help="显示插件信息")
    parser.add_argument("--function", help="指定要执行的函数名")
    parser.add_argument("--operation", help="操作类型")
    parser.add_argument("--source", help="数据源")
    parser.add_argument("--params", help="JSON格式的参数")
    
    args = parser.parse_args()
    
    try:
        debugger = PluginDebugger(args.plugin)
        
        if args.info:
            debugger.show_plugin_info()
            return
        
        # 准备参数
        kwargs = {}
        
        if args.operation:
            kwargs['operation'] = args.operation
        
        if args.source:
            kwargs['source'] = args.source
        
        if args.params:
            try:
                params = json.loads(args.params)
                kwargs.update(params)
            except json.JSONDecodeError as e:
                print(f"无效的JSON参数: {e}")
                return
        
        # 执行插件
        print(f"\n{'='*60}")
        print(f"执行插件: {args.plugin}")
        print(f"{'='*60}")
        
        result = debugger.execute_plugin(args.function, **kwargs)
        
        print(f"\n{'='*60}")
        print("执行结果:")
        print(f"{'='*60}")
        
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                elif isinstance(value, list) and len(value) > 3:
                    print(f"{key}: [{len(value)} items]")
                    for i, item in enumerate(value[:3]):
                        print(f"  [{i}]: {item}")
                    if len(value) > 3:
                        print(f"  ... and {len(value) - 3} more items")
                else:
                    print(f"{key}: {value}")
        else:
            print(result)
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        if "--verbose" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


'''
1. 查看插件信息
python scripts/debug_plugin.py data_pipeline --info
2. 执行插件的默认操作
python scripts/debug_plugin.py data_pipeline
3. 指定具体操作和参数
python scripts/debug_plugin.py data_pipeline --operation health_check
python scripts/debug_plugin.py data_pipeline --operation full_pipeline --source api
python scripts/debug_plugin.py data_pipeline --operation fetch_only --source database
4. 调用特定函数
python scripts/debug_plugin.py data_pipeline --function run_data_pipeline --operation stats
5. 传递复杂参数
python scripts/debug_plugin.py data_pipeline --params '{"operation": "full_pipeline", "batch_mode": true, "endpoints": ["teachers", "students"]}'
'''
if __name__ == "__main__":
    main() 