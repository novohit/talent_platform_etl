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
from contextlib import contextmanager

from talent_platform.config import config
from talent_platform.logger import logger

# 添加 dotenv 支持
try:
    from dotenv import load_dotenv, dotenv_values
except ImportError:
    # 如果没有安装 python-dotenv，创建简单的替代函数
    def load_dotenv(dotenv_path=None):
        pass
    
    def dotenv_values(dotenv_path=None):
        return {}


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
    env_vars: Dict[str, str] = None  # 插件环境变量
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.env_vars is None:
            self.env_vars = {}


@contextmanager
def plugin_environment(env_vars: Dict[str, str]):
    """
    插件环境变量上下文管理器
    临时设置插件的环境变量，执行完成后恢复原始环境
    """
    # 保存原始环境变量
    original_env = {}
    new_vars = []
    
    try:
        # 设置插件环境变量
        for key, value in env_vars.items():
            if key in os.environ:
                original_env[key] = os.environ[key]
            else:
                new_vars.append(key)
            os.environ[key] = value
        
        yield
        
    finally:
        # 恢复原始环境变量
        for key in new_vars:
            if key in os.environ:
                del os.environ[key]
        
        for key, value in original_env.items():
            os.environ[key] = value


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.virtual_envs: Dict[str, str] = {}
        self._lock = Lock()
        
        # 热加载相关
        self._hot_loader = None
        self.enable_hot_reload = True
        
        # 确保插件目录存在
        self.plugins_dir = Path(config.PLUGINS_DIR)
        self.venv_dir = Path(config.PLUGIN_VENV_DIR)
        self.plugins_dir.mkdir(exist_ok=True)
        self.venv_dir.mkdir(exist_ok=True)
        
        # 扫描并加载插件
        self._scan_plugins()
    
    def enable_hot_loading(self):
        """启用热加载功能"""
        try:
            from .plugin_hot_loader import get_hot_loader
            self._hot_loader = get_hot_loader()
            
            # 注册热加载回调
            self._hot_loader.register_callback("loaded", self._on_plugin_loaded)
            self._hot_loader.register_callback("unloaded", self._on_plugin_unloaded)
            self._hot_loader.register_callback("error", self._on_plugin_error)
            
            # 开始监听
            self._hot_loader.start_watching()
            
            self.enable_hot_reload = True
            logger.info("Plugin hot loading enabled")
            
        except Exception as e:
            logger.error(f"Failed to enable hot loading: {e}")
            self.enable_hot_reload = False
    
    def disable_hot_loading(self):
        """禁用热加载功能"""
        if self._hot_loader:
            self._hot_loader.stop_watching()
            self._hot_loader = None
        
        self.enable_hot_reload = False
        logger.info("Plugin hot loading disabled")
    
    def _on_plugin_loaded(self, plugin_name: str):
        """插件加载完成回调"""
        logger.info(f"Plugin hot loaded: {plugin_name}")
    
    def _on_plugin_unloaded(self, plugin_name: str):
        """插件卸载回调"""
        logger.info(f"Plugin unloaded: {plugin_name}")
    
    def _on_plugin_error(self, plugin_name: str, error_msg: str):
        """插件错误回调"""
        logger.error(f"Plugin error: {plugin_name} - {error_msg}")
    
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
        
        # 加载插件的环境变量
        plugin_env_file = plugin_dir / ".env"
        plugin_env_vars = {}
        
        if plugin_env_file.exists():
            try:
                # 读取插件的 .env 文件
                plugin_env_vars = dotenv_values(str(plugin_env_file))
                logger.info(f"Loaded {len(plugin_env_vars)} environment variables for plugin {metadata_dict['name']}")
            except Exception as e:
                logger.warning(f"Failed to load .env file for plugin {metadata_dict['name']}: {e}")
        
        # 将环境变量添加到元数据中
        if plugin_env_vars:
            metadata_dict['env_vars'] = plugin_env_vars
        
        metadata = PluginMetadata(**metadata_dict)
        self.plugins[metadata.name] = metadata
        
        logger.info(f"Loaded plugin metadata: {metadata.name} v{metadata.version}")
        if metadata.env_vars:
            logger.debug(f"Plugin {metadata.name} environment variables: {list(metadata.env_vars.keys())}")
    
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
            # 检查热加载更新
            if self.enable_hot_reload and self._hot_loader:
                try:
                    if not self._hot_loader.reload_if_updated(plugin_name):
                        logger.warning(f"Failed to hot reload plugin {plugin_name}")
                except Exception as e:
                    logger.error(f"Error during hot reload check for {plugin_name}: {e}")
            
            # 如果已经加载，直接返回
            if plugin_name in self.loaded_modules:
                return self.loaded_modules[plugin_name]
            
            return self._load_plugin_module(plugin_name)
    
    def _load_plugin_module(self, plugin_name: str) -> Optional[Any]:
        """内部模块加载方法，不进行热加载检查，避免递归调用"""
        # 如果已经加载，直接返回
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
        # 在执行前检查热加载更新
        if self.enable_hot_reload and self._hot_loader:
            try:
                if self._hot_loader.check_plugin_updates(plugin_name):
                    logger.info(f"Plugin {plugin_name} has updates, hot reloading...")
                    if not self._hot_loader.force_reload_plugin(plugin_name):
                        logger.warning(f"Hot reload failed for plugin {plugin_name}, using existing version")
            except Exception as e:
                logger.error(f"Error during hot reload for {plugin_name}: {e}")
        
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
            with plugin_environment(metadata.env_vars):
                result = plugin_function(**kwargs)
            logger.info(f"Plugin {plugin_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Plugin {plugin_name} execution failed: {e}")
            raise
    
    def force_reload_plugin(self, plugin_name: str) -> bool:
        """强制重新加载插件"""
        if self._hot_loader:
            return self._hot_loader.force_reload_plugin(plugin_name)
        else:
            # 简单重载逻辑
            if plugin_name in self.loaded_modules:
                del self.loaded_modules[plugin_name]
            
            # 重新加载元数据
            plugin_dir = self.plugins_dir / plugin_name
            if plugin_dir.exists():
                self._load_plugin_metadata(plugin_dir)
            
            # 重新加载模块
            module = self.load_plugin(plugin_name)
            return module is not None
    
    def get_plugin_hot_info(self, plugin_name: str) -> Dict:
        """获取插件热加载信息"""
        if self._hot_loader:
            return self._hot_loader.get_plugin_info(plugin_name)
        else:
            metadata = self.get_plugin_metadata(plugin_name)
            return {
                "name": plugin_name,
                "loaded": plugin_name in self.loaded_modules,
                "load_time": None,
                "checksum": None,
                "has_updates": False,
                "metadata": metadata,
                "hot_reload_enabled": False
            }
    
    def list_plugins_with_hot_info(self) -> List[Dict[str, Any]]:
        """列出所有插件及其热加载信息"""
        plugins_info = []
        
        for plugin_name in self.plugins.keys():
            info = self.get_plugin_hot_info(plugin_name)
            plugins_info.append(info)
        
        return plugins_info
    
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
        return self.force_reload_plugin(plugin_name)


# 全局插件管理器实例
plugin_manager = PluginManager() 