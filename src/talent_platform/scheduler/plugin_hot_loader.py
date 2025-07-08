"""
插件热加载管理器
支持在运行时动态加载、更新和卸载插件，无需重启worker
"""

import os
import sys
import json
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from talent_platform.config import config
from talent_platform.logger import logger


class PluginChangeHandler(FileSystemEventHandler):
    """插件文件变更处理器"""
    
    def __init__(self, hot_loader):
        self.hot_loader = hot_loader
        self.debounce_delay = 1.0  # 防抖延迟（秒）
        self.pending_changes = {}  # 待处理的变更
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        self._handle_file_change(event.src_path, "modified")
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        self._handle_file_change(event.src_path, "created")
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        
        self._handle_file_change(event.src_path, "deleted")
    
    def _handle_file_change(self, file_path: str, change_type: str):
        """处理文件变更事件（带防抖）"""
        current_time = time.time()
        
        # 只关心插件相关文件
        if not (file_path.endswith('.py') or file_path.endswith('.json')):
            return
        
        plugin_path = Path(file_path)
        plugin_name = None
        
        # 确定插件名
        for parent in plugin_path.parents:
            if parent.parent == Path(config.PLUGINS_DIR):
                plugin_name = parent.name
                break
        
        if not plugin_name:
            return
        
        # 防抖处理
        key = f"{plugin_name}:{change_type}"
        self.pending_changes[key] = {
            'plugin_name': plugin_name,
            'file_path': file_path,
            'change_type': change_type,
            'timestamp': current_time
        }
        
        # 延迟处理
        threading.Timer(
            self.debounce_delay,
            self._process_pending_change,
            args=[key, current_time]
        ).start()
    
    def _process_pending_change(self, key: str, timestamp: float):
        """处理待处理的变更"""
        if key not in self.pending_changes:
            return
        
        change = self.pending_changes[key]
        
        # 检查是否是最新的变更
        if change['timestamp'] != timestamp:
            return
        
        # 移除待处理项
        del self.pending_changes[key]
        
        # 处理变更
        self.hot_loader._handle_plugin_change(
            change['plugin_name'],
            change['file_path'],
            change['change_type']
        )


class PluginHotLoader:
    """插件热加载管理器"""
    
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager
        self.plugins_dir = Path(config.PLUGINS_DIR)
        
        # 插件状态追踪
        self.plugin_checksums = {}  # 插件文件校验和
        self.plugin_load_times = {}  # 插件加载时间
        self.plugin_dependencies = {}  # 插件依赖关系
        
        # 文件系统监听
        self.observer = None
        self.event_handler = None
        
        # 回调函数
        self.on_plugin_loaded = []  # 插件加载完成回调
        self.on_plugin_unloaded = []  # 插件卸载回调
        self.on_plugin_error = []  # 插件错误回调
        
        # 锁
        self._lock = threading.RLock()
        
        logger.info("Plugin hot loader initialized")
    
    def start_watching(self):
        """开始监听插件目录"""
        if self.observer is not None:
            logger.warning("Plugin watcher is already running")
            return
        
        try:
            self.event_handler = PluginChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                str(self.plugins_dir),
                recursive=True
            )
            self.observer.start()
            
            logger.info(f"Started watching plugin directory: {self.plugins_dir}")
            
            # 初始化插件校验和
            self._calculate_all_checksums()
            
        except Exception as e:
            logger.error(f"Failed to start plugin watcher: {e}")
            raise
    
    def stop_watching(self):
        """停止监听插件目录"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.event_handler = None
            logger.info("Stopped watching plugin directory")
    
    def register_callback(self, event_type: str, callback: Callable):
        """注册回调函数"""
        if event_type == "loaded":
            self.on_plugin_loaded.append(callback)
        elif event_type == "unloaded":
            self.on_plugin_unloaded.append(callback)
        elif event_type == "error":
            self.on_plugin_error.append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def force_reload_plugin(self, plugin_name: str) -> bool:
        """强制重新加载插件"""
        with self._lock:
            try:
                logger.info(f"Force reloading plugin: {plugin_name}")
                
                # 卸载现有插件
                self._unload_plugin(plugin_name)
                
                # 重新加载插件
                success = self._load_plugin(plugin_name)
                
                if success:
                    logger.info(f"Successfully force reloaded plugin: {plugin_name}")
                    self._trigger_callbacks("loaded", plugin_name)
                else:
                    logger.error(f"Failed to force reload plugin: {plugin_name}")
                    self._trigger_callbacks("error", plugin_name, "Force reload failed")
                
                return success
                
            except Exception as e:
                logger.error(f"Error during force reload of plugin {plugin_name}: {e}")
                self._trigger_callbacks("error", plugin_name, str(e))
                return False
    
    def check_plugin_updates(self, plugin_name: str) -> bool:
        """检查插件是否有更新"""
        with self._lock:
            try:
                current_checksum = self._calculate_plugin_checksum(plugin_name)
                stored_checksum = self.plugin_checksums.get(plugin_name)
                
                return current_checksum != stored_checksum
                
            except Exception as e:
                logger.error(f"Error checking updates for plugin {plugin_name}: {e}")
                return False
    
    def reload_if_updated(self, plugin_name: str) -> bool:
        """如果插件有更新则重新加载"""
        if self.check_plugin_updates(plugin_name):
            logger.info(f"Plugin {plugin_name} has updates, reloading...")
            return self.force_reload_plugin(plugin_name)
        return True
    
    def get_plugin_info(self, plugin_name: str) -> Dict:
        """获取插件信息"""
        with self._lock:
            return {
                "name": plugin_name,
                "loaded": plugin_name in self.plugin_manager.loaded_modules,
                "load_time": self.plugin_load_times.get(plugin_name),
                "checksum": self.plugin_checksums.get(plugin_name),
                "has_updates": self.check_plugin_updates(plugin_name),
                "metadata": self.plugin_manager.get_plugin_metadata(plugin_name)
            }
    
    def list_all_plugins(self) -> Dict:
        """列出所有插件的信息"""
        plugins_info = {}
        
        # 扫描插件目录
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
                plugin_name = plugin_dir.name
                plugins_info[plugin_name] = self.get_plugin_info(plugin_name)
        
        return plugins_info
    
    def _handle_plugin_change(self, plugin_name: str, file_path: str, change_type: str):
        """处理插件变更"""
        logger.info(f"Plugin change detected: {plugin_name} - {change_type} - {file_path}")
        
        try:
            if change_type in ["modified", "created"]:
                # 检查是否真的需要重新加载
                if self.check_plugin_updates(plugin_name):
                    self.force_reload_plugin(plugin_name)
                else:
                    logger.debug(f"No actual changes detected for plugin {plugin_name}")
            
            elif change_type == "deleted":
                # 处理文件删除
                if file_path.endswith("plugin.json"):
                    # 插件配置被删除，卸载插件
                    self._unload_plugin(plugin_name)
                    logger.info(f"Plugin {plugin_name} unloaded due to config deletion")
        
        except Exception as e:
            logger.error(f"Error handling plugin change for {plugin_name}: {e}")
            self._trigger_callbacks("error", plugin_name, str(e))
    
    def _load_plugin(self, plugin_name: str) -> bool:
        """加载单个插件"""
        try:
            # 重新扫描插件元数据
            plugin_dir = self.plugins_dir / plugin_name
            if not plugin_dir.exists() or not (plugin_dir / "plugin.json").exists():
                logger.warning(f"Plugin directory or config not found: {plugin_name}")
                return False

            # 加载元数据
            self.plugin_manager._load_plugin_metadata(plugin_dir)
            
            # 加载插件模块 - 使用内部方法避免递归调用
            module = self.plugin_manager._load_plugin_module(plugin_name)

            if module:
                # 更新状态
                self.plugin_load_times[plugin_name] = datetime.now()
                self.plugin_checksums[plugin_name] = self._calculate_plugin_checksum(plugin_name)
                logger.info(f"Successfully hot reloaded plugin: {plugin_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def _unload_plugin(self, plugin_name: str):
        """卸载插件"""
        try:
            # 从插件管理器中移除
            if plugin_name in self.plugin_manager.loaded_modules:
                del self.plugin_manager.loaded_modules[plugin_name]
            
            if plugin_name in self.plugin_manager.plugins:
                del self.plugin_manager.plugins[plugin_name]
            
            # 清理模块缓存
            modules_to_remove = []
            for module_name in sys.modules:
                if module_name.startswith(f"plugin_{plugin_name}"):
                    modules_to_remove.append(module_name)
            
            for module_name in modules_to_remove:
                del sys.modules[module_name]
            
            # 清理状态
            self.plugin_load_times.pop(plugin_name, None)
            self.plugin_checksums.pop(plugin_name, None)
            
            logger.info(f"Plugin {plugin_name} unloaded")
            self._trigger_callbacks("unloaded", plugin_name)
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
    
    def _calculate_plugin_checksum(self, plugin_name: str) -> str:
        """计算插件文件校验和"""
        plugin_dir = self.plugins_dir / plugin_name
        if not plugin_dir.exists():
            return ""
        
        hasher = hashlib.md5()
        
        # 计算所有相关文件的校验和
        for file_path in plugin_dir.rglob("*.py"):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        
        for file_path in plugin_dir.rglob("*.json"):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def _calculate_all_checksums(self):
        """计算所有插件的校验和"""
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
                plugin_name = plugin_dir.name
                self.plugin_checksums[plugin_name] = self._calculate_plugin_checksum(plugin_name)
    
    def _trigger_callbacks(self, event_type: str, plugin_name: str, error_msg: str = None):
        """触发回调函数"""
        callbacks = []
        if event_type == "loaded":
            callbacks = self.on_plugin_loaded
        elif event_type == "unloaded":
            callbacks = self.on_plugin_unloaded
        elif event_type == "error":
            callbacks = self.on_plugin_error
        
        for callback in callbacks:
            try:
                if event_type == "error":
                    callback(plugin_name, error_msg)
                else:
                    callback(plugin_name)
            except Exception as e:
                logger.error(f"Error in callback for {event_type}: {e}")


# 全局热加载管理器实例
hot_loader = None

def get_hot_loader():
    """获取全局热加载管理器实例"""
    global hot_loader
    if hot_loader is None:
        from .plugin_manager import plugin_manager
        hot_loader = PluginHotLoader(plugin_manager)
    return hot_loader 