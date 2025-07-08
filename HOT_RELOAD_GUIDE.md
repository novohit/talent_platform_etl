# 插件热加载功能指南

## 🔥 概述

插件热加载功能允许你在不停止 worker 的情况下，动态更新和重载插件。这对于生产环境的持续部署和开发环境的快速迭代非常有用。

## 🚀 核心特性

### 1. 自动文件监听

- 监听插件目录的文件变更
- 支持 `.py`、`.json` 和 `.env` 文件的变更检测
- 插件级 `.env` 文件变更会触发热重载
- 全局 `plugins/.env` 文件不会触发热重载（避免影响所有插件）
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

### 2. 环境变量热加载演示 🔥

**步骤 1：创建环境变量文件**

```bash
# 复制环境变量配置模板
cp plugins/hot_reload_demo/config.env.example plugins/hot_reload_demo/.env

# 查看初始配置
cat plugins/hot_reload_demo/.env
```

**步骤 2：测试初始环境变量**

```bash
# 运行环境变量热加载测试
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --operation test_env_hot_reload
```

你会看到类似输出：

```
===============================================================================
🔥 环境变量热加载测试
===============================================================================
📋 当前环境变量配置：
   HOT_RELOAD_TEST_MESSAGE = '环境变量热加载测试消息'
   TEST_ITERATION_COUNT = 3
   OUTPUT_COLOR_THEME = blue
```

**步骤 3：修改环境变量**

编辑 `plugins/hot_reload_demo/.env` 文件：

```bash
# 修改测试消息
HOT_RELOAD_TEST_MESSAGE=这是更新后的测试消息！

# 修改迭代次数
TEST_ITERATION_COUNT=5

# 修改颜色主题
OUTPUT_COLOR_THEME=green

# 启用调试输出
ENABLE_DEBUG_OUTPUT=true
```

**步骤 4：验证热加载生效**

```bash
# 再次运行测试，会自动使用新的环境变量
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --operation test_env_hot_reload
```

你会看到：

- 🟢 颜色主题已改为绿色
- 测试消息已更新
- 迭代次数增加到 5 次
- 启用了调试输出

### 3. 代码热加载演示

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

### 4. 环境变量热加载特别注意 🔥

- **插件级配置优先**：插件目录内的 `.env` 文件会覆盖全局配置
- **全局配置保护**：修改 `plugins/.env` 不会触发热重载，避免影响所有插件
- **配置验证**：环境变量变更后应验证插件是否正常工作
- **敏感信息管理**：确保 `.env` 文件不被意外提交到版本控制
- **类型转换**：环境变量都是字符串，注意在代码中进行适当的类型转换

### 5. 错误处理

- 如果新版本插件有错误，系统会记录日志但不会崩溃
- 可以通过回滚插件文件来恢复
- 环境变量格式错误不会导致插件加载失败，但可能影响功能

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
- 利用环境变量热加载快速调整配置参数

### 2. 生产环境

- 谨慎使用热加载，确保充分测试
- 建立回滚机制
- 监控系统性能影响
- 环境变量变更前进行备份

### 3. 插件开发

- 保持插件接口稳定
- 避免在插件中使用全局状态
- 合理处理初始化和清理逻辑

### 4. 环境变量管理 🔥

- **分层配置**：全局通用配置放在 `plugins/.env`，插件特定配置放在插件目录
- **配置文档**：为每个环境变量添加注释说明
- **默认值处理**：在代码中提供合理的默认值
- **类型安全**：使用适当的类型转换和验证
- **敏感信息保护**：使用 `.env.example` 文件提供模板，真实配置不提交到版本控制

```python
# 推荐的环境变量使用模式
def get_env_int(key: str, default: int) -> int:
    """安全获取整数环境变量"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(f"Invalid integer value for {key}, using default: {default}")
        return default

def get_env_bool(key: str, default: bool) -> bool:
    """安全获取布尔环境变量"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on', 'enabled')

# 使用示例
batch_size = get_env_int('BATCH_SIZE', 100)
debug_enabled = get_env_bool('DEBUG_MODE', False)
```

## 🎉 总结

热加载功能让你的插件系统更加灵活和强大，现在支持：

- ✅ **代码热加载** - `.py` 和 `.json` 文件变更自动重载
- ✅ **环境变量热加载** - 插件级 `.env` 文件变更自动重载
- ✅ **全局配置保护** - `plugins/.env` 文件不会触发热重载
- ✅ **智能监听** - 防抖机制和内容校验避免无效重载
- ✅ **安全隔离** - 插件重载失败不影响其他插件

**快速开始环境变量热加载：**

```bash
# 1. 复制配置模板
cp plugins/hot_reload_demo/config.env.example plugins/hot_reload_demo/.env

# 2. 测试初始配置
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --operation test_env_hot_reload

# 3. 修改 .env 文件中的任何值

# 4. 再次测试，新配置自动生效
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --operation test_env_hot_reload
```

在享受便利的同时，请注意合理使用和监控系统状态。🚀
