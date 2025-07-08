# 调度系统使用指南

## 概述

这是一个基于 Celery 的统一调度系统，支持插件式管理第三方脚本，具有以下特性：

- 🚀 **异步任务调度**: 基于 Celery 的分布式任务队列
- 🔌 **插件系统**: 动态加载和管理第三方处理脚本
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

## 系统架构

```
调度系统
├── Celery App (任务队列)
├── Plugin Manager (插件管理)
├── Database Monitor (数据库监听)
├── Task Scheduler (任务调度)
└── 插件目录
    ├── data_processor/
    │   ├── plugin.json
    │   └── main.py
    └── es_indexer/
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
# 启动 Worker (处理任务)
python -m talent_platform.scheduler_app worker

# 启动 Beat (定时任务调度器)
python -m talent_platform.scheduler_app beat

# 启动监控 (可选)
python -m talent_platform.scheduler_app monitor
```

### 4. 测试插件

```bash
# 列出所有插件
python -m talent_platform.scheduler_app list-plugins

# 测试插件
python -m talent_platform.scheduler_app test-plugin data_processor

# 触发插件执行
python -m talent_platform.scheduler_app trigger data_processor --operation sync_data
```

## 插件开发

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

## 数据库变更监听

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

## API 使用

### 通过代码调用

```python
from talent_platform.scheduler import task_scheduler, plugin_manager

# 直接执行插件
result = plugin_manager.execute_plugin(
    "data_processor",
    operation="sync_data",
    sync_type="manual"
)

# 异步触发插件
task_id = task_scheduler.trigger_plugin(
    "data_processor",
    {"operation": "sync_data"},
    priority="high"
)

# 获取任务状态
status = task_scheduler.get_task_status(task_id)

# 系统健康检查
health = task_scheduler.health_check()
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

## 示例插件

项目包含两个示例插件：

1. **data_processor**: 数据处理插件，演示如何处理爬虫数据
2. **es_indexer**: ES 索引插件，演示如何管理 Elasticsearch 索引

你可以参考这些示例来开发自己的插件。

## 联系支持

如有问题或建议，请联系开发团队或提交 Issue。
