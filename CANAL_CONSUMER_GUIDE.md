# 🚇 Canal 数据库变更消费者系统

## 📋 概述

Canal 消费者系统基于阿里 Canal，实时监听 MySQL 数据库的 binlog 变更，并自动触发相应的插件处理任务。系统设计简约而通用，支持多消费者并行处理。

## 🏗️ 系统架构

```
MySQL Database
    ↓ (binlog)
Canal Server
    ↓ (TCP)
CanalClient
    ↓ (events)
ConsumerManager
    ↓ (dispatch)
Multiple Consumers → trigger_plugin() → TaskScheduler → Plugins
```

## 📁 目录结构

```
src/talent_platform/consumers/
├── __init__.py              # 包初始化
├── canal_client.py          # Canal客户端封装
├── base_consumer.py         # 基础消费者类
├── consumer_manager.py      # 消费者管理器
├── consumer_app.py         # 启动脚本
├── config.py               # 配置文件
└── consumers/              # 具体消费者实现
    ├── __init__.py
    ├── teacher_consumer.py  # 教师数据消费者
    └── example_consumer.py  # 示例消费者
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Canal Python客户端
pip install python-canal-client
```

### 2. 启动消费者

```bash
# 基本启动
python -m talent_platform.consumers.consumer_app start

# 自定义配置启动
python -m talent_platform.consumers.consumer_app start \
    --host 172.12.0.13 \
    --port 11111 \
    --destination example
```

### 3. 查看状态

```bash
# 列出所有消费者
python -m talent_platform.consumers.consumer_app list

# 查看系统状态
python -m talent_platform.consumers.consumer_app status
```

## 🎯 核心功能

### 数据库变更处理流程

1. **接收 Canal 事件** - 解析 binlog 事件
2. **事件分发** - 分发给相关消费者
3. **过滤匹配** - 根据表过滤器判断
4. **触发插件** - 调用 task_scheduler.trigger_plugin()

### 多消费者支持

- **并行处理** - 多消费者同时处理不同表
- **独立配置** - 每个消费者独立的过滤器
- **灵活启停** - 可单独启用/禁用消费者

## 💻 命令行工具

### 基本命令

```bash
# 启动消费者服务
python -m talent_platform.consumers.consumer_app start [options]

# 列出所有消费者
python -m talent_platform.consumers.consumer_app list

# 查看系统状态
python -m talent_platform.consumers.consumer_app status

# 启用/禁用消费者
python -m talent_platform.consumers.consumer_app enable teacher_consumer
python -m talent_platform.consumers.consumer_app disable example_consumer

# 测试消费者
python -m talent_platform.consumers.consumer_app test teacher_consumer
```

## 🔧 开发自定义消费者

### 创建消费者类

```python
from ..base_consumer import BaseConsumer
from ..canal_client import ChangeEvent

class MyConsumer(BaseConsumer):
    def __init__(self):
        super().__init__("my_consumer")

        # 配置要监听的表
        self.add_filter("my_db", "users", {"INSERT", "UPDATE"})
        self.add_filter("my_db", "orders", {"INSERT"})

    def process_event(self, event: ChangeEvent):
        """处理数据库变更事件"""
        if event.table == "users":
            self._handle_user_change(event)
        elif event.table == "orders":
            self._handle_order_change(event)

    def _handle_user_change(self, event: ChangeEvent):
        if event.event_type == "INSERT":
            # 新用户注册，触发欢迎邮件
            self.trigger_plugin("email_service", {
                "operation": "send_welcome",
                "user_id": event.data.get("id")
            })

    def _handle_order_change(self, event: ChangeEvent):
        # 新订单，触发订单处理
        self.trigger_plugin("order_processor", {
            "operation": "process_new_order",
            "order_id": event.data.get("id")
        }, priority="high")
```

## 🔍 配置和监控

### 环境变量配置

```bash
export CANAL_HOST=172.12.0.13
export CANAL_PORT=11111
export CANAL_DESTINATION=example
export CANAL_BATCH_SIZE=100
```

### 监控命令

```bash
# 实时状态监控
watch -n 5 'python -m talent_platform.consumers.consumer_app status'

# 查看日志
tail -f logs/app.log | grep "Consumer\|Canal"
```

## 📊 示例消费者

### TeacherConsumer (教师数据消费者)

```python
# 监听表:
- talent_platform.derived_intl_teacher_data
- talent_platform.data_intl_wide_view
- talent_platform.teacher_profiles

# 触发插件:
- data_processor: 数据处理
- es_indexer: ES索引更新
- error_handler: 错误处理
```

### ExampleConsumer (示例消费者)

```python
# 监听表:
- test_db.users (INSERT, UPDATE)
- test_db.orders (INSERT)

# 触发插件:
- email_service: 邮件服务
- order_processor: 订单处理
```

## 🚨 故障排除

### Canal 连接失败

```bash
# 检查Canal服务状态
telnet 172.12.0.13 11111

# 检查binlog是否开启
SHOW VARIABLES LIKE 'log_bin';
```

### 插件触发失败

```bash
# 检查插件状态
python -m talent_platform.scheduler_app list-plugins

# 启动Worker
python -m talent_platform.scheduler_app worker --queues plugin_tasks
```

## 🎉 总结

Canal 消费者系统提供：

- ✅ **实时性** - 基于 binlog 的实时监听
- ✅ **可扩展** - 支持自定义消费者
- ✅ **高可用** - 自动重连和错误处理
- ✅ **易集成** - 与任务调度系统无缝集成
- ✅ **简约设计** - 清晰架构和简单 API

通过这个系统，你可以轻松实现数据库变更的实时响应处理。
