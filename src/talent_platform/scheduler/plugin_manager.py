import os
import sys
import json
import importlib
import importlib.util
import subprocess
import venv
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from threading import Lock

from talent_platform.config import config
from talent_platform.logger import logger


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    entry_point: str  # 入口函数路径，如 "main.process_data"
    parameters: Dict[str, Any]  # 参数定义
    dependencies: List[str]  # 依赖包列表
    python_version: str = ">=3.8"
    enabled: bool = True
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.virtual_envs: Dict[str, str] = {}
        self._lock = Lock()
        
        # 确保插件目录存在
        self.plugins_dir = Path(config.PLUGINS_DIR)
        self.venv_dir = Path(config.PLUGIN_VENV_DIR)
        self.plugins_dir.mkdir(exist_ok=True)
        self.venv_dir.mkdir(exist_ok=True)
        
        # 扫描并加载插件
        self._scan_plugins()
    
    def _scan_plugins(self):
        """扫描插件目录，加载插件元数据"""
        logger.info(f"Scanning plugins in {self.plugins_dir}")
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
                try:
                    self._load_plugin_metadata(plugin_dir)
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_dir.name}: {e}")
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    def _load_plugin_metadata(self, plugin_dir: Path):
        """加载单个插件的元数据"""
        metadata_file = plugin_dir / "plugin.json"
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_dict = json.load(f)
        
        metadata = PluginMetadata(**metadata_dict)
        self.plugins[metadata.name] = metadata
        
        logger.info(f"Loaded plugin metadata: {metadata.name} v{metadata.version}")
    
    def _create_virtual_env(self, plugin_name: str, dependencies: List[str]) -> str:
        """为插件创建虚拟环境"""
        venv_path = self.venv_dir / plugin_name
        
        if venv_path.exists():
            logger.info(f"Virtual environment already exists for {plugin_name}")
            return str(venv_path)
        
        logger.info(f"Creating virtual environment for {plugin_name}")
        
        # 创建虚拟环境
        venv.create(venv_path, with_pip=True)
        
        # 安装依赖
        if dependencies:
            pip_path = venv_path / "bin" / "pip"
            if not pip_path.exists():  # Windows
                pip_path = venv_path / "Scripts" / "pip.exe"
            
            for dependency in dependencies:
                logger.info(f"Installing {dependency} for {plugin_name}")
                subprocess.run([str(pip_path), "install", dependency], check=True)
        
        self.virtual_envs[plugin_name] = str(venv_path)
        return str(venv_path)
    
    def load_plugin(self, plugin_name: str) -> Optional[Any]:
        """加载插件模块"""
        with self._lock:
            if plugin_name in self.loaded_modules:
                return self.loaded_modules[plugin_name]
            
            if plugin_name not in self.plugins:
                logger.error(f"Plugin {plugin_name} not found")
                return None
            
            metadata = self.plugins[plugin_name]
            if not metadata.enabled:
                logger.warning(f"Plugin {plugin_name} is disabled")
                return None
            
            try:
                # 创建虚拟环境（如果需要）
                if metadata.dependencies:
                    venv_path = self._create_virtual_env(plugin_name, metadata.dependencies)
                    # 将虚拟环境的 site-packages 添加到 sys.path
                    site_packages = Path(venv_path) / "lib" / "python3.13" / "site-packages"
                    if not site_packages.exists():  # Windows
                        site_packages = Path(venv_path) / "Lib" / "site-packages"
                    
                    if site_packages.exists():
                        sys.path.insert(0, str(site_packages))
                
                # 加载插件模块
                plugin_dir = self.plugins_dir / plugin_name
                module_path = plugin_dir / (metadata.entry_point.split('.')[0] + '.py')
                
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{plugin_name}",
                    module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                self.loaded_modules[plugin_name] = module
                logger.info(f"Successfully loaded plugin: {plugin_name}")
                
                return module
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                return None
    
    def get_plugin_function(self, plugin_name: str) -> Optional[Callable]:
        """获取插件的入口函数"""
        module = self.load_plugin(plugin_name)
        if not module:
            return None
        
        metadata = self.plugins[plugin_name]
        function_name = metadata.entry_point.split('.')[-1]
        
        if hasattr(module, function_name):
            return getattr(module, function_name)
        else:
            logger.error(f"Function {function_name} not found in plugin {plugin_name}")
            return None
    
    def execute_plugin(self, plugin_name: str, **kwargs) -> Any:
        """执行插件"""
        plugin_function = self.get_plugin_function(plugin_name)
        if not plugin_function:
            raise ValueError(f"Cannot load plugin function for {plugin_name}")
        
        metadata = self.plugins[plugin_name]
        
        # 验证参数
        missing_params = []
        for param_name, param_config in metadata.parameters.items():
            if param_config.get('required', False) and param_name not in kwargs:
                missing_params.append(param_name)
        
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        logger.info(f"Executing plugin {plugin_name} with parameters: {list(kwargs.keys())}")
        
        try:
            result = plugin_function(**kwargs)
            logger.info(f"Plugin {plugin_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Plugin {plugin_name} execution failed: {e}")
            raise
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return [asdict(metadata) for metadata in self.plugins.values()]
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        return self.plugins.get(plugin_name)
    
    def enable_plugin(self, plugin_name: str):
        """启用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            logger.info(f"Plugin {plugin_name} enabled")
    
    def disable_plugin(self, plugin_name: str):
        """禁用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            if plugin_name in self.loaded_modules:
                del self.loaded_modules[plugin_name]
            logger.info(f"Plugin {plugin_name} disabled")
    
    def reload_plugin(self, plugin_name: str):
        """重新加载插件"""
        if plugin_name in self.loaded_modules:
            del self.loaded_modules[plugin_name]
        
        # 重新加载元数据
        plugin_dir = self.plugins_dir / plugin_name
        if plugin_dir.exists():
            self._load_plugin_metadata(plugin_dir)
        
        # 重新加载模块
        self.load_plugin(plugin_name)
        logger.info(f"Plugin {plugin_name} reloaded")


# 全局插件管理器实例
plugin_manager = PluginManager() 