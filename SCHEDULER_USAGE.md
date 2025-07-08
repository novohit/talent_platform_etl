# 统一调度系统使用指南

## 🎯 概述

这是一个基于 Celery 的统一调度系统，支持插件式管理第三方脚本，具有以下特性：

- 🚀 **异步任务调度**: 基于 Celery 的分布式任务队列
- 🔌 **插件系统**: 动态加载和管理第三方处理脚本
- 🔥 **热加载功能**: 不停机更新插件代码，支持实时开发
- 📊 **数据库监听**: 自动监听数据库变更并触发相应处理
- 📦 **依赖管理**: 为每个插件独立管理 Python 依赖
- 🎯 **任务调度**: 支持定时任务、触发式任务和批量任务
- 📈 **监控和日志**: 完整的任务执行监控和日志记录

## 环境配置

首先创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/talent_platform
DOMAIN_TREE_DATABASE_URL=mysql+pymysql://user:password@localhost:3306/domain_tree

# Elasticsearch 配置
ES_HOSTS=http://localhost:9200
ES_USERNAME=elastic
ES_PASSWORD=your_es_password
ES_TIMEOUT=30

# Redis 和 Celery 配置
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 插件系统配置
PLUGINS_DIR=plugins
PLUGIN_VENV_DIR=plugin_envs

# 数据库变更监听配置
DB_CHANGE_POLLING_INTERVAL=5
```

## 🏗️ 系统架构

```
调度系统
├── Celery App (任务队列)
├── Plugin Manager (插件管理)
├── Hot Loader (热加载管理)
├── Database Monitor (数据库监听)
├── Task Scheduler (任务调度)
└── 插件目录
    ├── data_processor/
    │   ├── plugin.json
    │   └── main.py
    ├── es_indexer/
    │   ├── plugin.json
    │   └── main.py
    └── hot_reload_demo/
        ├── plugin.json
        └── main.py
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或使用 uv
uv sync
```

### 2. 启动 Redis

```bash
redis-server
```

### 3. 启动调度系统

```bash
# 启动完整的调度服务（包含热加载）
./start_scheduler.sh start

# 查看服务状态
./start_scheduler.sh status

# 停止服务
./start_scheduler.sh stop
```

### 4. 基本操作

```bash
# 查看所有插件
python -m talent_platform.scheduler_app list-plugins

# 查看插件热加载状态
python -m talent_platform.scheduler_app list-plugins-hot

# 测试插件
python -m talent_platform.scheduler_app test-plugin data_processor

# 触发异步任务
python -m talent_platform.scheduler_app trigger es_indexer --operation bulk_index

# 系统健康检查
python -m talent_platform.scheduler_app health
```

## 🔧 插件开发

### 创建新插件

**1. 创建插件目录：**

```bash
mkdir plugins/my_plugin
cd plugins/my_plugin
```

**2. 创建配置文件 `plugin.json`：**

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "我的自定义插件",
  "author": "Your Name",
  "entry_point": "main.process_data",
  "parameters": {
    "operation": { "type": "string", "required": true },
    "data_source": { "type": "string", "required": false, "default": "default" }
  },
  "dependencies": ["requests>=2.30.0", "pandas>=2.0.0"],
  "python_version": ">=3.8",
  "enabled": true,
  "tags": ["data", "processing"]
}
```

**3. 创建主要代码 `main.py`：**

```python
"""
我的自定义插件
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def process_data(operation: str, data_source: str = "default", **kwargs) -> Dict[str, Any]:
    """
    数据处理入口函数

    Args:
        operation: 操作类型
        data_source: 数据源
        **kwargs: 其他参数

    Returns:
        处理结果字典
    """
    logger.info(f"Processing {operation} from {data_source}")

    # 你的业务逻辑
    result = {
        "operation": operation,
        "data_source": data_source,
        "processed_records": 100,
        "success": True
    }

    return {
        "status": "success",
        "operation": operation,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
```

**4. 测试插件：**

```bash
# 测试新插件
python -m talent_platform.scheduler_app test-plugin my_plugin --operation sync_data

# 如果修改了代码，可以热重载
python -m talent_platform.scheduler_app reload my_plugin
```

### 插件目录结构

```
plugins/
└── your_plugin/
    ├── plugin.json     # 插件配置
    ├── main.py         # 主要代码
    └── requirements.txt # 依赖 (可选)
```

### 插件配置文件 (plugin.json)

```json
{
  "name": "your_plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "author": "Your Name",
  "entry_point": "main.your_function",
  "parameters": {
    "param1": {
      "type": "string",
      "required": true,
      "description": "参数描述"
    },
    "param2": {
      "type": "integer",
      "required": false,
      "default": 100
    }
  },
  "dependencies": ["requests>=2.30.0", "pandas>=2.0.0"],
  "python_version": ">=3.8",
  "enabled": true,
  "tags": ["data-processing", "crawler"]
}
```

### 插件代码示例 (main.py)

```python
def your_function(param1: str, param2: int = 100, **kwargs):
    """
    插件主函数

    Args:
        param1: 必需参数
        param2: 可选参数
        **kwargs: 其他参数，包括 change_event 等

    Returns:
        Dict: 处理结果
    """

    # 你的处理逻辑
    result = {
        "processed_data": f"Processed {param1} with {param2}",
        "status": "success"
    }

    return {
        "status": "success",
        "operation": "your_operation",
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
```

## 🔥 热加载功能

### 核心特性

- ✅ **自动文件监听**：监听插件目录变更
- ✅ **智能更新检测**：基于 MD5 校验和避免无意义重载
- ✅ **安全的模块管理**：清理缓存，保持系统稳定
- ✅ **任务执行时检查**：确保使用最新版本代码

### 基本使用

```bash
# 查看热加载状态
python -m talent_platform.scheduler_app list-plugins-hot

# 手动启用/禁用热加载
python -m talent_platform.scheduler_app enable-hot-reload
python -m talent_platform.scheduler_app disable-hot-reload

# 监听插件变更（阻塞模式）
python -m talent_platform.scheduler_app watch

# 强制重新加载插件
python -m talent_platform.scheduler_app reload plugin_name
```

### 热加载演示

**1. 测试演示插件：**

```bash
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --message "测试消息"
```

**2. 修改插件代码：**
编辑 `plugins/hot_reload_demo/main.py` 中的任何内容

**3. 再次测试（自动使用新版本）：**

```bash
python -m talent_platform.scheduler_app test-plugin hot_reload_demo --message "更新后的消息"
```

**详细热加载指南请参考：** `HOT_RELOAD_GUIDE.md`

## 📋 命令参考

### 系统管理

| 命令      | 说明           | 示例                                              |
| --------- | -------------- | ------------------------------------------------- |
| `worker`  | 启动 Worker    | `python -m talent_platform.scheduler_app worker`  |
| `beat`    | 启动定时调度器 | `python -m talent_platform.scheduler_app beat`    |
| `monitor` | 启动监控       | `python -m talent_platform.scheduler_app monitor` |
| `health`  | 系统健康检查   | `python -m talent_platform.scheduler_app health`  |

### 插件管理

| 命令               | 说明               | 示例                                                                 |
| ------------------ | ------------------ | -------------------------------------------------------------------- |
| `list-plugins`     | 列出所有插件       | `python -m talent_platform.scheduler_app list-plugins`               |
| `list-plugins-hot` | 列出插件热加载状态 | `python -m talent_platform.scheduler_app list-plugins-hot`           |
| `test-plugin`      | 测试插件           | `python -m talent_platform.scheduler_app test-plugin data_processor` |
| `trigger`          | 触发插件执行       | `python -m talent_platform.scheduler_app trigger es_indexer`         |
| `reload`           | 重新加载插件       | `python -m talent_platform.scheduler_app reload my_plugin`           |

### 热加载管理

| 命令                 | 说明         | 示例                                                         |
| -------------------- | ------------ | ------------------------------------------------------------ |
| `enable-hot-reload`  | 启用热加载   | `python -m talent_platform.scheduler_app enable-hot-reload`  |
| `disable-hot-reload` | 禁用热加载   | `python -m talent_platform.scheduler_app disable-hot-reload` |
| `watch`              | 监听插件变更 | `python -m talent_platform.scheduler_app watch`              |

### 任务管理

| 命令     | 说明         | 示例                                                     |
| -------- | ------------ | -------------------------------------------------------- |
| `status` | 查看任务状态 | `python -m talent_platform.scheduler_app status task_id` |

## 📊 数据库变更监听

系统会自动监听配置的数据库表变更，并触发相应的插件处理：

```python
# 在 db_monitor.py 中配置监听的表
monitored_tables = {
    "your_table": {
        "triggers": ["your_plugin"],  # 触发的插件
        "conditions": {"status": "active"},  # 触发条件
        "operations": ["INSERT", "UPDATE"]   # 监听的操作
    }
}
```

## 🚀 高级用法

### 1. 编程式插件调用

```python
from talent_platform.scheduler import plugin_manager, task_scheduler

# 同步执行插件
result = plugin_manager.execute_plugin(
    "data_processor",
    operation="sync_data",
    teacher_id="123"
)

# 异步执行插件
task_id = task_scheduler.trigger_plugin(
    "es_indexer",
    {
        "operation": "update_index",
        "teacher_id": "123",
        "data": {"name": "John Doe"}
    }
)

# 检查任务状态
status = task_scheduler.get_task_status(task_id)
```

### 2. 热加载编程接口

```python
from talent_platform.scheduler.plugin_manager import plugin_manager

# 检查插件是否有更新
has_updates = plugin_manager._hot_loader.check_plugin_updates("my_plugin")

# 强制重载插件
success = plugin_manager.force_reload_plugin("my_plugin")

# 获取插件热加载信息
info = plugin_manager.get_plugin_hot_info("my_plugin")
```

### 3. 数据库监听配置

```python
# 在 config.py 中配置监听的表
DB_MONITOR_TABLES = [
    {
        "table": "teachers",
        "plugin": "es_indexer",
        "operation": "update_teacher_index",
        "condition": "is_valid = 1"
    }
]
```

### 4. 自定义队列

```bash
# 启动指定队列的worker
python -m talent_platform.scheduler_app worker --queues high_priority,plugin_tasks

# 启动高并发worker
python -m talent_platform.scheduler_app worker --concurrency 8
```

### 命令行工具

```bash
# 系统状态
python -m talent_platform.scheduler_app health

# 插件管理
python -m talent_platform.scheduler_app list-plugins
python -m talent_platform.scheduler_app test-plugin your_plugin
python -m talent_platform.scheduler_app trigger your_plugin --operation your_op

# 任务状态
python -m talent_platform.scheduler_app status <task_id>

# 启动服务
python -m talent_platform.scheduler_app worker --queues plugin_tasks --concurrency 4
python -m talent_platform.scheduler_app beat
```

## 高级功能

### 批量任务执行

```python
plugin_configs = [
    {
        "plugin_name": "data_processor",
        "parameters": {"operation": "sync_data", "sync_type": "daily"}
    },
    {
        "plugin_name": "es_indexer",
        "parameters": {"operation": "bulk_index", "batch_size": 1000}
    }
]

task_id = task_scheduler.batch_trigger_plugins(plugin_configs)
```

### 定时任务配置

```python
# 添加定时任务
task_config = {
    "id": "daily_sync",
    "name": "每日数据同步",
    "plugin_name": "data_processor",
    "parameters": {"operation": "sync_data", "sync_type": "daily"},
    "schedule_type": "cron",
    "schedule_config": {"cron": "0 2 * * *"}  # 每天凌晨2点
}

task_scheduler.add_scheduled_task(task_config)
```

### 插件热更新

```python
# 重新加载插件
plugin_manager.reload_plugin("your_plugin")

# 启用/禁用插件
plugin_manager.enable_plugin("your_plugin")
plugin_manager.disable_plugin("your_plugin")
```

## 监控和调试

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

### Celery 监控

```bash
# 查看 Worker 状态
celery -A talent_platform.scheduler.celery_app status

# 查看活动任务
celery -A talent_platform.scheduler.celery_app inspect active

# 查看任务统计
celery -A talent_platform.scheduler.celery_app inspect stats
```

## 常见问题

### Q: 如何处理插件依赖冲突？

A: 系统为每个插件创建独立的虚拟环境，避免依赖冲突。

### Q: 如何监听更多数据库表？

A: 在 `db_monitor.py` 的 `monitored_tables` 中添加配置。

### Q: 插件执行失败怎么办？

A: 系统支持自动重试，可以在任务中配置重试次数和间隔。

### Q: 如何扩展系统？

A: 可以增加更多 Worker 实例来提高处理能力，支持分布式部署。

## 📖 示例插件

系统包含以下示例插件：

1. **data_processor**: 数据处理插件，演示如何处理爬虫数据
2. **es_indexer**: ES 索引插件，演示如何管理 Elasticsearch 索引
3. **hot_reload_demo**: 热加载演示插件，展示热加载功能

你可以参考这些示例来开发自己的插件。

## 🐛 故障排除

### 常见问题

**1. 插件无法加载**

```bash
# 检查插件配置
cat plugins/plugin_name/plugin.json

# 查看详细日志
tail -f logs/app.log | grep plugin_name
```

**2. 热加载不工作**

```bash
# 检查热加载状态
python -m talent_platform.scheduler_app list-plugins-hot

# 手动重载
python -m talent_platform.scheduler_app reload plugin_name
```

**3. 任务执行失败**

```bash
# 查看任务状态
python -m talent_platform.scheduler_app status task_id

# 检查系统健康
python -m talent_platform.scheduler_app health
```

**4. 依赖问题**

```bash
# 检查虚拟环境
ls -la plugin_envs/plugin_name/

# 重新安装依赖
rm -rf plugin_envs/plugin_name/
python -m talent_platform.scheduler_app test-plugin plugin_name
```

### 日志监控

```bash
# 实时监控调度系统日志
tail -f logs/app.log

# 监控插件相关日志
tail -f logs/app.log | grep -E "(plugin|reload|hot)"

# 监控错误日志
tail -f logs/error.log
```

## 📞 技术支持

如果遇到问题，请：

1. 查看详细日志文件
2. 运行系统健康检查
3. 参考故障排除指南
4. 查看 `HOT_RELOAD_GUIDE.md` 了解热加载详情

---

**快速链接：**

- 🔥 [热加载详细指南](HOT_RELOAD_GUIDE.md)
- 📋 [系统设计文档](SCHEDULER_SUMMARY.md)
- 🚀 [启动脚本使用](start_scheduler.sh)
