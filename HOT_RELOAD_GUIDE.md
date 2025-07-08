# 插件热加载功能指南

## 🔥 概述

插件热加载功能允许你在不停止 worker 的情况下，动态更新和重载插件。这对于生产环境的持续部署和开发环境的快速迭代非常有用。

## 🚀 核心特性

### 1. 自动文件监听

- 监听插件目录的文件变更
- 支持 `.py` 和 `.json` 文件的变更检测
- 防抖机制避免频繁重载

### 2. 智能更新检测

- 基于文件内容 MD5 校验和检测真实变更
- 避免无意义的重载操作
- 跟踪插件加载时间和版本

### 3. 安全的插件卸载

- 清理模块缓存
- 移除过期的插件实例
- 保持系统稳定性

### 4. 任务执行时检查

- 在执行插件前自动检查更新
- 确保使用最新版本的插件代码
- 透明的热加载过程

## 🛠️ 使用方法

### 自动启用（推荐）

系统启动时会自动启用热加载功能：

```bash
# 启动worker时会自动启用热加载
./start_scheduler.sh start
```

### 手动控制

```bash
# 启用热加载
python -m talent_platform.scheduler_app enable-hot-reload

# 禁用热加载
python -m talent_platform.scheduler_app disable-hot-reload

# 查看热加载状态
python -m talent_platform.scheduler_app list-plugins-hot
```

### 监听模式

```bash
# 启动专门的监听进程（阻塞模式）
python -m talent_platform.scheduler_app watch
```

### 手动重载

```bash
# 强制重新加载特定插件
python -m talent_platform.scheduler_app reload plugin_name

# 查看插件状态
python -m talent_platform.scheduler_app list-plugins-hot
```

## 📝 热加载演示

### 1. 创建演示环境

```bash
# 查看现有插件
python -m talent_platform.scheduler_app list-plugins-hot

# 测试演示插件
python -m talent_platform.scheduler_app test-plugin hot_reload_demo
```

### 2. 实时更新演示

**步骤 1：运行初始版本**

```bash
# 测试原始版本
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --message "Initial version"
```

输出会显示版本 1.0 的结果。

**步骤 2：修改插件代码**

编辑 `plugins/hot_reload_demo/main.py`，修改版本和功能：

```python
def demo_function(message: str = "Hello from hot reload demo!",
                 count: int = 1,
                 **kwargs) -> Dict[str, Any]:
    """
    演示函数 - 版本 2.0 (热加载更新)
    """

    logger.info(f"Hot reload demo v2.0 - UPDATED VERSION!")

    # 新增功能：添加时间戳
    results = []
    for i in range(count):
        timestamp = datetime.now().strftime("%H:%M:%S")
        result_message = f"[{i+1}] {message} (Updated at {timestamp})"
        results.append(result_message)

    response = {
        "status": "success",
        "operation": "demo_function",
        "version": "2.0",  # 更新版本号
        "plugin_info": {
            "name": "hot_reload_demo",
            "version": "2.0",
            "description": "这是热加载更新后的版本！"  # 更新描述
        },
        "result": {
            "input_message": message,
            "input_count": count,
            "generated_messages": results,
            "total_messages": len(results),
            "processing_time": "~0.1s",
            "update_note": "此版本通过热加载自动更新！"  # 新增字段
        },
        "timestamp": datetime.now().isoformat()
    }

    return response
```

**步骤 3：验证热加载**

```bash
# 再次测试，应该自动使用新版本
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --message "Updated version"

# 查看热加载状态
python -m talent_platform.scheduler_app list-plugins-hot
```

你会看到：

- 版本从 1.0 更新到 2.0
- 输出包含新增的时间戳和更新说明
- 插件状态显示已重新加载

## 🔧 高级功能

### 1. 编程式热加载控制

```python
from talent_platform.scheduler.plugin_manager import plugin_manager

# 检查插件是否有更新
has_updates = plugin_manager._hot_loader.check_plugin_updates("my_plugin")

# 强制重载插件
success = plugin_manager.force_reload_plugin("my_plugin")

# 获取插件热加载信息
info = plugin_manager.get_plugin_hot_info("my_plugin")
print(f"Plugin loaded: {info['loaded']}")
print(f"Has updates: {info['has_updates']}")
print(f"Load time: {info['load_time']}")
```

### 2. 回调函数注册

```python
from talent_platform.scheduler.plugin_hot_loader import get_hot_loader

hot_loader = get_hot_loader()

# 注册热加载事件回调
def on_plugin_loaded(plugin_name):
    print(f"Plugin {plugin_name} has been loaded!")

def on_plugin_error(plugin_name, error_msg):
    print(f"Plugin {plugin_name} error: {error_msg}")

hot_loader.register_callback("loaded", on_plugin_loaded)
hot_loader.register_callback("error", on_plugin_error)
```

### 3. 生产环境配置

```python
# 配置文件监听间隔
DB_CHANGE_POLLING_INTERVAL=5

# 在高负载环境下可能需要调整防抖延迟
# 修改 plugin_hot_loader.py 中的 debounce_delay
```

## ⚠️ 注意事项

### 1. 内存考虑

- 频繁的插件重载可能增加内存使用
- 建议在低峰期进行大量插件更新

### 2. 并发安全

- 热加载过程中会加锁，避免并发问题
- 正在执行的任务不会被中断

### 3. 依赖管理

- 如果插件依赖发生变化，可能需要重启 worker
- 建议将依赖变更和代码变更分开处理

### 4. 错误处理

- 如果新版本插件有错误，系统会记录日志但不会崩溃
- 可以通过回滚插件文件来恢复

## 🐛 故障排除

### 问题 1：热加载不工作

**检查步骤：**

```bash
# 1. 确认热加载状态
python -m talent_platform.scheduler_app list-plugins-hot

# 2. 查看系统日志
tail -f logs/app.log | grep -i "hot"

# 3. 手动触发重载
python -m talent_platform.scheduler_app reload plugin_name
```

### 问题 2：插件更新后仍是旧版本

**可能原因：**

- 文件没有真正变更（内容相同）
- 缓存问题
- 权限问题

**解决方法：**

```bash
# 强制重载
python -m talent_platform.scheduler_app reload plugin_name

# 检查文件权限
ls -la plugins/plugin_name/

# 重启热加载监听
python -m talent_platform.scheduler_app disable-hot-reload
python -m talent_platform.scheduler_app enable-hot-reload
```

### 问题 3：性能影响

**优化建议：**

- 调整防抖延迟时间
- 减少不必要的文件写入
- 使用更精确的文件监听

## 📊 监控和指标

### 热加载统计

```bash
# 查看详细状态
python -m talent_platform.scheduler_app list-plugins-hot

# 系统健康检查
python -m talent_platform.scheduler_app health
```

### 日志监控

```bash
# 监听热加载相关日志
tail -f logs/app.log | grep -E "(hot|reload|plugin.*load)"

# 错误日志
tail -f logs/error.log | grep -i plugin
```

## 🎯 最佳实践

### 1. 开发环境

- 启用热加载以快速测试代码变更
- 使用监听模式实时查看更新

### 2. 生产环境

- 谨慎使用热加载，确保充分测试
- 建立回滚机制
- 监控系统性能影响

### 3. 插件开发

- 保持插件接口稳定
- 避免在插件中使用全局状态
- 合理处理初始化和清理逻辑

热加载功能让你的插件系统更加灵活和强大，在享受便利的同时，请注意合理使用和监控系统状态。
