# 数据管道插件 (Data Pipeline Plugin)

这是一个复杂的多包结构数据处理管道插件，展示了调度系统支持的高级插件架构。

## 🏗️ 架构概览

```
plugins/data_pipeline/
├── utils/              # 工具包
│   ├── logger.py      # 日志管理
│   ├── helpers.py     # 辅助函数
│   └── decorators.py  # 装饰器
├── config/            # 配置包
│   └── settings.py    # 配置管理
├── fetchers/          # 数据获取包
│   ├── api_fetcher.py      # API数据获取
│   ├── database_fetcher.py # 数据库数据获取
│   └── file_fetcher.py     # 文件数据获取
├── processors/        # 数据处理包
│   ├── data_cleaner.py     # 数据清洗
│   ├── data_transformer.py # 数据转换
│   └── data_validator.py   # 数据验证
├── storage/           # 数据存储包
│   ├── database_storage.py # 数据库存储
│   ├── file_storage.py     # 文件存储
│   └── cache_storage.py    # 缓存存储
├── main.py            # 主入口
├── plugin.json        # 插件配置
└── config.env.example # 环境变量示例
```

## ✨ 主要特性

### 🔧 多包架构

- **utils**: 提供日志、辅助函数、装饰器等通用工具
- **config**: 完整的配置管理系统，支持环境变量和验证
- **fetchers**: 多数据源获取支持（API、数据库、文件）
- **processors**: 数据处理管道（清洗、转换、验证）
- **storage**: 多存储方案（数据库、文件、缓存）

### 🚀 高级功能

- **完整的 ETL 流程**: 获取 → 处理 → 存储
- **多数据源支持**: API、数据库、文件
- **装饰器支持**: 计时、重试、缓存、速率限制等
- **配置管理**: 分层配置，环境变量支持
- **错误处理**: 完善的错误处理和恢复机制
- **监控指标**: 执行统计、性能监控
- **健康检查**: 组件状态监控

## 🎯 支持的操作

### 1. 完整管道 (full_pipeline)

```bash
python -m talent_platform.scheduler_app trigger data_pipeline --operation full_pipeline --source api --endpoint teachers
```

### 2. 仅数据获取 (fetch_only)

```bash
python -m talent_platform.scheduler_app trigger data_pipeline --operation fetch_only --source database --table teachers
```

### 3. 健康检查 (health_check)

```bash
python -m talent_platform.scheduler_app trigger data_pipeline --operation health_check
```

### 4. 配置信息 (config_info)

```bash
python -m talent_platform.scheduler_app trigger data_pipeline --operation config_info
```

### 5. 统计信息 (stats)

```bash
python -m talent_platform.scheduler_app trigger data_pipeline --operation stats
```

## ⚙️ 配置说明

### 环境变量配置

复制 `config.env.example` 为 `.env` 并根据需要修改：

```bash
# 基础配置
PLUGIN_NAME=data_pipeline
LOG_LEVEL=INFO
DEBUG_MODE=true

# API配置
API_BASE_URL=https://api.example.com
API_TIMEOUT=30
API_RETRIES=3

# 数据库配置
DB_HOST=localhost
DB_NAME=talent_platform
DB_USER=pipeline_user
DB_PASSWORD=your_password

# 处理配置
BATCH_SIZE=100
MAX_WORKERS=4
EXECUTION_MODE=sequential
```

### 操作参数

#### full_pipeline 参数

- `source`: 数据源类型 (api/database/file)
- `endpoint`: API 端点 (当 source=api 时)
- `table`: 数据表名 (当 source=database 时)
- `file_path`: 文件路径 (当 source=file 时)
- `batch_mode`: 是否启用批处理模式

#### fetch_only 参数

- `source`: 数据源类型 (必需)
- `params`: 请求参数 (可选)

## 📊 使用示例

### 1. API 数据处理

```python
# 从API获取教师数据并处理
result = plugin_manager.execute_plugin(
    "data_pipeline",
    operation="full_pipeline",
    source="api",
    endpoint="teachers",
    params={"page": 1, "limit": 50}
)
```

### 2. 数据库批量处理

```python
# 从数据库获取数据并批量处理
result = plugin_manager.execute_plugin(
    "data_pipeline",
    operation="full_pipeline",
    source="database",
    table="teachers",
    limit=100
)
```

### 3. 文件数据处理

```python
# 处理CSV文件数据
result = plugin_manager.execute_plugin(
    "data_pipeline",
    operation="full_pipeline",
    source="file",
    file_path="teachers.csv",
    format="csv"
)
```

## 🔍 监控与调试

### 健康检查

```python
health = plugin_manager.execute_plugin(
    "data_pipeline",
    operation="health_check"
)
print(f"Pipeline status: {health['pipeline_status']}")
```

### 性能统计

```python
stats = plugin_manager.execute_plugin(
    "data_pipeline",
    operation="stats"
)
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average execution time: {stats['average_execution_time_formatted']}")
```

## 🔄 调度任务

插件支持预定义的调度任务：

- **daily_teacher_sync**: 每日凌晨 2 点同步教师数据
- **hourly_health_check**: 每小时执行健康检查

可通过调度系统管理界面启用/禁用这些任务。

## 🛠️ 扩展开发

### 添加新的数据获取器

1. 在 `fetchers/` 目录创建新的获取器类
2. 继承基础接口并实现 `fetch()` 方法
3. 在 `__init__.py` 中导出新类
4. 在主管道中集成

### 添加新的处理器

1. 在 `processors/` 目录创建新的处理器类
2. 实现数据处理逻辑
3. 集成到主处理流程中

### 自定义配置

1. 在 `config/settings.py` 中添加新的配置类
2. 更新环境变量解析
3. 在 `plugin.json` 中声明新的环境变量

## 📝 日志说明

插件使用分层日志系统：

- **DEBUG**: 详细的执行步骤
- **INFO**: 关键操作和结果
- **WARNING**: 非致命问题
- **ERROR**: 错误和异常

日志格式支持标准格式和 JSON 格式，可通过 `LOG_FORMAT` 环境变量控制。

## 🔐 安全考虑

- 数据库密码等敏感信息通过环境变量配置
- 支持数据验证和清洗，防止注入攻击
- 配置验证确保系统安全运行
- 错误信息不包含敏感数据

---
