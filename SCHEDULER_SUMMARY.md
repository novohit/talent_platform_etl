# 统一调度系统设计总结

## 🎯 项目目标

基于你的需求，我设计并实现了一个完整的统一调度系统，解决以下核心问题：

1. **统一管理零散的 Python 处理脚本**
2. **基于 Celery 的异步任务调度**
3. **监听数据库变更自动触发处理**
4. **插件式管理第三方脚本**
5. **独立的依赖环境管理**
6. **通过反射方式调用第三方脚本**

## 🏗️ 系统架构

### 核心组件

| 组件                 | 文件位置                                          | 职责                   |
| -------------------- | ------------------------------------------------- | ---------------------- |
| **Celery App**       | `src/talent_platform/scheduler/celery_app.py`     | 任务队列和分布式调度   |
| **Plugin Manager**   | `src/talent_platform/scheduler/plugin_manager.py` | 插件动态加载和依赖管理 |
| **Database Monitor** | `src/talent_platform/scheduler/db_monitor.py`     | 数据库变更监听         |
| **Task Scheduler**   | `src/talent_platform/scheduler/task_scheduler.py` | 统一任务调度管理       |
| **Celery Tasks**     | `src/talent_platform/scheduler/tasks.py`          | 异步任务定义           |
| **管理工具**         | `src/talent_platform/scheduler_app.py`            | 命令行管理接口         |

### 插件生态

```
plugins/
├── data_processor/          # 数据处理插件
│   ├── plugin.json         # 插件元数据配置
│   └── main.py            # 插件实现代码
└── es_indexer/             # ES索引插件
    ├── plugin.json
    └── main.py
```

## 🔧 核心功能实现

### 1. 插件系统 (Plugin System)

**特性:**

- ✅ 动态加载插件代码
- ✅ 独立虚拟环境管理
- ✅ 插件元数据配置
- ✅ 参数验证和类型检查
- ✅ 插件热重载
- ✅ 反射式函数调用

**插件配置示例:**

```json
{
  "name": "data_processor",
  "version": "1.0.0",
  "entry_point": "main.process_data",
  "parameters": {
    "operation": { "type": "string", "required": true },
    "teacher_id": { "type": "string", "required": false }
  },
  "dependencies": ["pandas>=2.0.0", "requests>=2.30.0"]
}
```

### 2. 数据库变更监听 (Database Monitoring)

**特性:**

- ✅ 配置化表监听
- ✅ 变更事件触发
- ✅ 条件过滤机制
- ✅ 自动插件调用

**监听配置示例:**

```python
monitored_tables = {
    "derived_intl_teacher_data": {
        "triggers": ["data_processor", "es_indexer"],
        "conditions": {"is_valid": True},
        "operations": ["INSERT", "UPDATE"]
    }
}
```

### 3. 异步任务调度 (Celery Integration)

**特性:**

- ✅ 基于 Redis 的消息队列
- ✅ 多队列任务分发
- ✅ 任务重试机制
- ✅ 定时任务支持
- ✅ 任务状态监控

**队列配置:**

- `plugin_tasks`: 插件执行任务
- `monitoring`: 数据库监听任务
- `high_priority`: 高优先级任务

### 4. 依赖管理 (Dependency Management)

**特性:**

- ✅ 为每个插件创建独立虚拟环境
- ✅ 自动安装插件依赖
- ✅ 避免依赖冲突
- ✅ 动态环境切换

**实现机制:**

```python
# 为插件创建虚拟环境
venv_path = self.venv_dir / plugin_name
venv.create(venv_path, with_pip=True)

# 安装依赖
for dependency in dependencies:
    subprocess.run([pip_path, "install", dependency])
```

### 5. 统一管理接口 (Management Interface)

**命令行工具:**

```bash
# 系统管理
./start_scheduler.sh start           # 启动所有服务
./start_scheduler.sh status          # 查看系统状态
./start_scheduler.sh stop            # 停止服务

# 插件管理
python -m talent_platform.scheduler_app list-plugins
python -m talent_platform.scheduler_app test-plugin data_processor
python -m talent_platform.scheduler_app trigger es_indexer
```

## 📊 数据流程

1. **数据库变更** → Database Monitor 检测变更
2. **变更事件** → 根据配置触发相应插件
3. **任务队列** → Celery 将任务分发给 Worker
4. **插件执行** → Plugin Manager 加载并执行插件
5. **结果处理** → 写入日志，更新状态

## 🚀 使用示例

### 快速启动

```bash
# 1. 启动Redis
redis-server

# 2. 启动调度系统
./start_scheduler.sh start

# 3. 测试插件
python -m talent_platform.scheduler_app test-plugin data_processor
```

### 开发自定义插件

1. **创建插件目录**

```bash
mkdir -p plugins/my_crawler
```

2. **配置插件元数据**

```json
{
  "name": "my_crawler",
  "entry_point": "main.crawl_data",
  "parameters": {
    "url": { "type": "string", "required": true },
    "pages": { "type": "integer", "default": 10 }
  },
  "dependencies": ["requests", "beautifulsoup4"]
}
```

3. **实现插件代码**

```python
def crawl_data(url: str, pages: int = 10, **kwargs):
    # 你的爬虫逻辑
    return {
        "status": "success",
        "pages_crawled": pages,
        "data_count": 100
    }
```

4. **使用插件**

```bash
python -m talent_platform.scheduler_app trigger my_crawler \
  --url "https://example.com" --pages 5
```

### 集成到现有代码

```python
from talent_platform.scheduler import task_scheduler, plugin_manager

# 同步执行
result = plugin_manager.execute_plugin(
    "data_processor",
    operation="sync_data"
)

# 异步执行
task_id = task_scheduler.trigger_plugin(
    "my_crawler",
    {"url": "https://example.com", "pages": 10}
)
```

## 🎨 系统特色

### 1. 零侵入式集成

- 第三方脚本无需修改现有代码
- 只需提供入口函数和参数定义
- 通过配置文件进行集成

### 2. 强大的隔离机制

- 每个插件独立的 Python 环境
- 避免依赖冲突
- 插件故障不影响系统稳定性

### 3. 灵活的调度策略

- 支持数据库触发式调度
- 支持定时任务调度
- 支持手动触发调度
- 支持批量任务调度

### 4. 完善的监控体系

- 实时任务状态监控
- 详细的执行日志
- 插件性能指标
- 系统健康检查

### 5. 易于扩展

- 插件热插拔
- 水平扩展支持
- 分布式部署能力

## 📈 生产环境部署

### 高可用部署

```bash
# 启动多个Worker实例
python -m talent_platform.scheduler_app worker --concurrency 4 &
python -m talent_platform.scheduler_app worker --concurrency 4 &

# 启动Beat调度器
python -m talent_platform.scheduler_app beat &

# 启动监控服务
python -m talent_platform.scheduler_app monitor &
```

### 监控和运维

```bash
# 查看任务状态
celery -A talent_platform.scheduler.celery_app inspect active

# 查看Worker状态
celery -A talent_platform.scheduler.celery_app status

# 系统健康检查
python -m talent_platform.scheduler_app health
```

## 🔮 未来扩展方向

1. **Web 管理界面**: 可视化插件管理和任务监控
2. **更多数据源**: 支持消息队列、文件监听等触发方式
3. **插件市场**: 插件分享和版本管理机制
4. **性能优化**: 任务并行度优化和资源使用监控
5. **安全增强**: 插件沙箱执行和权限控制

## 📝 总结

这个统一调度系统完全满足你的需求：

✅ **统一调度**: 基于 Celery 的强大调度能力  
✅ **数据库监听**: 自动监听变更并触发处理  
✅ **插件管理**: 零侵入式管理第三方脚本  
✅ **依赖隔离**: 独立环境避免冲突  
✅ **反射调用**: 动态加载和执行函数  
✅ **易于使用**: 丰富的管理工具和文档

系统设计遵循了模块化、可扩展、高可用的原则，为处理爬虫数据的零散脚本提供了一个强大而灵活的统一调度平台。
