# 简洁数据库调度器使用指南

## 🎯 概述

本方案**重新设计**了 Celery Beat 数据库调度器，抛弃了复杂的"激进重置"机制，采用**简洁而可靠**的实现方式。

### 核心特性

- ✅ **简洁设计**：代码清晰易懂，维护简单
- ✅ **MySQL 持久化**：任务配置存储在数据库，重启后完全恢复
- ✅ **变更检测**：通过哈希机制检测任务变更，30 秒内生效
- ✅ **完整功能**：支持任务启用/禁用、参数修改、调度配置变更
- ✅ **高效缓存**：智能缓存机制，减少数据库查询

## 🏗️ 架构设计

```
SimpleDatabaseScheduler
├── 调度表缓存 (_schedule_cache)
├── 变更检测 (30秒检查周期)
├── 哈希比较 (MD5算法)
└── 数据库同步 (MySQLr读取)

数据流：
MySQL数据库 → 哈希检测 → 缓存更新 → Celery Beat执行
```

### 关键组件

1. **SimpleDatabaseScheduleEntry** - 任务条目
2. **SimpleDatabaseScheduler** - 调度器主体
3. **哈希变更检测** - 核心变更检测逻辑

## 📊 数据库模型

使用现有的 `ScheduledTaskModel`：

```sql
CREATE TABLE scheduled_tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    parameters JSON DEFAULT '{}',
    schedule_type VARCHAR(20) NOT NULL,    -- 'interval' 或 'cron'
    schedule_config JSON NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,

    last_run DATETIME NULL,
    next_run DATETIME NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    description VARCHAR(500) NULL,
    priority INT DEFAULT 5,
    max_retries INT DEFAULT 3,
    timeout INT NULL
);
```

## 🚀 使用方法

### 1. 启动服务

#### 启动 Worker

```bash
celery -A src.talent_platform.scheduler.celery_app worker --loglevel=info --concurrency=4
```

#### 启动 Beat 调度器

```bash
celery -A src.talent_platform.scheduler.celery_app beat --loglevel=info
```

### 2. 添加任务

#### 间隔调度任务

```python
from talent_platform.db.database import get_scheduler_db_session
from talent_platform.db.models import ScheduledTaskModel

task_data = {
    "id": "health_check_task",
    "name": "数据库健康检查",
    "plugin_name": "mysql_test",
    "parameters": {"operation": "health_check"},
    "schedule_type": "interval",
    "schedule_config": {"interval": 300},  # 每5分钟
    "enabled": True,
    "description": "定期检查数据库连接状态",
    "priority": 8
}

with get_scheduler_db_session() as session:
    task = ScheduledTaskModel(**task_data)
    session.add(task)
    session.commit()
```

#### Cron 调度任务

```python
task_data = {
    "id": "daily_report_task",
    "name": "每日报表生成",
    "plugin_name": "data_processor",
    "parameters": {"operation": "generate_daily_report"},
    "schedule_type": "cron",
    "schedule_config": {
        "minute": "0",
        "hour": "9",           # 每天上午9点
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*"
    },
    "enabled": True
}
```

### 3. 管理任务

#### 禁用任务

```python
with get_scheduler_db_session() as session:
    task = session.get(ScheduledTaskModel, "health_check_task")
    task.enabled = False
    task.updated_at = datetime.now()
    session.add(task)
    session.commit()
```

⏱️ **检测时间**: 30 秒内生效

#### 重新启用任务

```python
with get_scheduler_db_session() as session:
    task = session.get(ScheduledTaskModel, "health_check_task")
    task.enabled = True
    task.updated_at = datetime.now()
    session.add(task)
    session.commit()
```

⏱️ **检测时间**: 30 秒内生效

#### 修改任务参数

```python
with get_scheduler_db_session() as session:
    task = session.get(ScheduledTaskModel, "health_check_task")
    task.parameters = {"operation": "detailed_check", "timeout": 60}
    task.updated_at = datetime.now()
    session.add(task)
    session.commit()
```

⏱️ **检测时间**: 30 秒内生效

#### 修改调度配置

```python
with get_scheduler_db_session() as session:
    task = session.get(ScheduledTaskModel, "health_check_task")
    task.schedule_config = {"interval": 180}  # 改为每3分钟
    task.updated_at = datetime.now()
    session.add(task)
    session.commit()
```

⏱️ **检测时间**: 30 秒内生效

## 🔍 变更检测机制

### 检测方式

- **检查频率**: 每 30 秒检查一次
- **检测方法**: MD5 哈希值比较
- **检测内容**: 所有任务的所有关键字段

### 哈希计算包含字段

```python
task_data = {
    'id': task.id,
    'name': task.name,
    'plugin_name': task.plugin_name,
    'parameters': task.parameters,
    'schedule_type': task.schedule_type,
    'schedule_config': task.schedule_config,
    'enabled': task.enabled,
    'priority': task.priority,
    'max_retries': task.max_retries,
    'timeout': task.timeout,
    'updated_at': task.updated_at.isoformat()
}
```

### 性能优化

- ✅ **智能缓存**: 无变化时返回缓存，不查询数据库
- ✅ **高效检测**: 仅对启用任务计算哈希
- ✅ **最小查询**: 30 秒检查周期，避免频繁数据库访问

## 🧪 测试验证

运行测试脚本验证功能：

```bash
python test_simple_scheduler.py
```

测试覆盖：

- ✅ 基本功能：任务加载、调度表构建
- ✅ 变更检测：参数修改检测
- ✅ 启用/禁用：任务状态变更检测

## 📋 日志输出

### 正常运行日志

```
[INFO] SimpleDatabaseScheduler initialized
[INFO] Database schedule setup completed
[INFO] Loaded 3 enabled tasks from database
[INFO] Schedule updated with 3 tasks
```

### 变更检测日志

```
[INFO] Tasks changed detected: a1b2c3d4 -> e5f6g7h8
[INFO] Schedule updated with 4 tasks
```

### 任务执行日志

```
[DEBUG] Updated last_run for task: health_check_task
```

## ⚡ 性能特点

- **启动时间**: 快速（无复杂初始化）
- **内存使用**: 低（简洁缓存机制）
- **数据库查询**: 高效（30 秒周期 + 智能缓存）
- **变更响应**: 快速（30 秒内检测）

## 🆚 对比旧方案

| 特性       | 简洁方案 | 激进重置方案 |
| ---------- | -------- | ------------ |
| 代码复杂度 | ✅ 简洁  | ❌ 复杂      |
| 维护难度   | ✅ 容易  | ❌ 困难      |
| 性能消耗   | ✅ 低    | ❌ 高        |
| 稳定性     | ✅ 稳定  | ⚠️ 激进      |
| 功能完整性 | ✅ 完整  | ✅ 完整      |

## 🔧 配置选项

在 `celery_app.py` 中的关键配置：

```python
celery_app.conf.update(
    # 使用简洁数据库调度器
    beat_scheduler='talent_platform.scheduler.simple_database_scheduler:SimpleDatabaseScheduler',

    # 调度器检查频率（可选调整）
    beat_max_loop_interval=5.0,  # 每5秒唤醒一次
)
```

## 🎯 总结

简洁数据库调度器提供了：

1. **可靠的 MySQL 持久化** - 任务配置完全存储在数据库
2. **有效的变更检测** - 30 秒内检测并应用所有变更
3. **简洁的代码实现** - 易于理解和维护
4. **高效的性能表现** - 智能缓存减少数据库查询

这是一个**生产就绪**的解决方案，替代了复杂的激进重置机制，提供稳定可靠的定时任务调度功能。
