# 🚫 任务取消指南

## 📋 概述

当你使用 `python -m talent_platform.scheduler_app trigger long_time_test` 启动任务后，如果需要取消正在运行的任务，可以使用以下方法。

## 🛠️ 取消任务的方法

### 方法一：通过任务 ID 取消

#### 1. 查看活动任务

首先查看当前所有正在运行的任务：

```bash
python -m talent_platform.scheduler_app list-active
```

输出示例：

```
============================================================
活动任务列表
============================================================
Worker 数量: 1
任务总数: 2

Worker: celery@hostname
任务数: 2
----------------------------------------
  任务ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  任务名: talent_platform.scheduler.tasks.execute_plugin_task
  插件名: long_time_test
  参数: ['long_time_test']

  任务ID: b2c3d4e5-f6g7-8901-bcde-f23456789012
  任务名: talent_platform.scheduler.tasks.execute_plugin_task
  插件名: mysql_test
  参数: ['mysql_test']

========================================
```

#### 2. 取消指定任务

使用任务 ID 取消特定任务：

```bash
python -m talent_platform.scheduler_app cancel a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

输出示例：

```
============================================================
取消任务: a1b2c3d4-e5f6-7890-abcd-ef1234567890
============================================================
✓ 任务已成功取消
```

### 方法二：取消指定插件的所有任务

如果你想取消 `long_time_test` 插件的所有运行中任务：

```bash
python -m talent_platform.scheduler_app cancel-plugin long_time_test
```

输出示例：

```
============================================================
取消插件任务: long_time_test
============================================================
✓ 已取消 2 个 long_time_test 插件的任务
已取消的任务ID:
  - a1b2c3d4-e5f6-7890-abcd-ef1234567890
  - c3d4e5f6-g7h8-9012-cdef-345678901234
```

### 方法三：使用 Celery 命令行直接操作

如果上述方法不可用，你也可以直接使用 Celery 命令：

#### 1. 查看活动任务

```bash
celery -A src.talent_platform.scheduler.celery_app inspect active
```

#### 2. 取消任务

```bash
celery -A src.talent_platform.scheduler.celery_app control revoke <task_id> --terminate
```

## 🔍 查看任务状态

在取消之前或之后，你可以检查任务的状态：

```bash
python -m talent_platform.scheduler_app status <task_id>
```

输出示例：

```
============================================================
任务状态: a1b2c3d4-e5f6-7890-abcd-ef1234567890
============================================================
状态: REVOKED
```

可能的状态包括：

- `PENDING`: 等待执行
- `STARTED`: 正在执行
- `SUCCESS`: 执行成功
- `FAILURE`: 执行失败
- `REVOKED`: 已取消

## 📝 完整流程示例

假设你刚刚启动了一个 `long_time_test` 任务：

```bash
# 1. 启动任务
python -m talent_platform.scheduler_app trigger long_time_test
# 输出: 任务已提交，任务ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

# 2. 查看活动任务
python -m talent_platform.scheduler_app list-active

# 3. 取消任务（选择其中一种方法）
# 方法A: 通过任务ID
python -m talent_platform.scheduler_app cancel a1b2c3d4-e5f6-7890-abcd-ef1234567890

# 方法B: 取消所有 long_time_test 任务
python -m talent_platform.scheduler_app cancel-plugin long_time_test

# 4. 验证任务已取消
python -m talent_platform.scheduler_app status a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## ⚠️ 注意事项

1. **已完成的任务无法取消**：如果任务已经执行完成（SUCCESS/FAILURE），则无法取消。

2. **terminate 参数**：使用 `terminate=True` 会强制终止正在运行的任务，这可能会导致数据不一致，请谨慎使用。

3. **Worker 必须在线**：任务取消需要 Celery Worker 在线才能生效。

4. **定时任务 vs 触发任务**：
   - 通过 `trigger` 启动的是一次性任务
   - 通过 `add-task` 添加的是定时任务，需要用 `disable-task` 来禁用

## 🆘 故障排除

### 问题：取消命令无响应

**解决方案**：

```bash
# 检查 Worker 状态
celery -A src.talent_platform.scheduler.celery_app inspect ping

# 检查是否有 Worker 在运行
python -m talent_platform.scheduler_app worker --queues plugin_tasks
```

### 问题：任务仍在运行

**解决方案**：

```bash
# 使用更强制的方式
celery -A src.talent_platform.scheduler.celery_app control revoke <task_id> --terminate --signal=SIGKILL
```

### 问题：找不到任务 ID

**解决方案**：

- 检查 `trigger` 命令的输出，任务 ID 在那里显示
- 或者使用 `cancel-plugin` 命令取消所有该插件的任务

## 🎯 总结

最简单的取消 `long_time_test` 任务的方法：

```bash
# 快速取消所有 long_time_test 任务
python -m talent_platform.scheduler_app cancel-plugin long_time_test
```

这个命令会自动找到并取消所有正在运行的 `long_time_test` 任务，无需手动查找任务 ID。
