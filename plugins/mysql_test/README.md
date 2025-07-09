# MySQL 连接测试插件

这是一个用于测试 MySQL 数据库连接和基本操作的示例插件，展示了如何在插件中使用环境变量配置。

## 🚀 功能特性

- **连接测试**: 测试 MySQL 数据库连接是否正常
- **查询测试**: 执行基本查询验证数据库功能
- **健康检查**: 检查数据库服务状态和性能指标
- **表信息**: 获取数据库表列表和详细信息
- **统计信息**: 记录和显示测试统计数据

## 📋 依赖要求

- Python >= 3.8
- PyMySQL >= 1.0.2
- cryptography >= 3.4.8

## ⚙️ 配置说明

### 1. 创建环境配置文件

复制环境配置模板并修改连接信息：

```bash
cp plugins/mysql_test/config.env.example plugins/mysql_test/.env
```

### 2. 配置 MySQL 连接信息

编辑 `.env` 文件，设置您的 MySQL 连接参数：

```bash
# MySQL连接配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_CHARSET=utf8mb4

# 连接池配置
MYSQL_MAX_CONNECTIONS=10
MYSQL_CONNECTION_TIMEOUT=30
MYSQL_READ_TIMEOUT=30
MYSQL_WRITE_TIMEOUT=30

# SSL配置（可选）
MYSQL_SSL_DISABLED=true
MYSQL_SSL_CA=
MYSQL_SSL_CERT=
MYSQL_SSL_KEY=

# 其他配置
MYSQL_AUTOCOMMIT=true
MYSQL_USE_UNICODE=true
```

## 🔧 使用方法

### 1. 直接运行插件

```bash
cd plugins/mysql_test
python main.py
```

### 2. 使用调试工具

```bash
# 查看插件信息
python scripts/debug_plugin.py mysql_test --info

# 测试连接
python scripts/debug_plugin.py mysql_test --operation test_connection

# 查询测试
python scripts/debug_plugin.py mysql_test --operation query_test

# 健康检查
python scripts/debug_plugin.py mysql_test --operation health_check

# 显示数据库表
python scripts/debug_plugin.py mysql_test --operation show_tables

# 查看统计信息
python scripts/debug_plugin.py mysql_test --operation stats
```

### 3. 通过调度系统运行

```bash
# 测试插件
python -m talent_platform.scheduler_app test-plugin mysql_test

# 触发特定操作
python -m talent_platform.scheduler_app trigger mysql_test --operation health_check
```

## 📊 操作类型

| 操作              | 描述         | 示例                       |
| ----------------- | ------------ | -------------------------- |
| `test_connection` | 基本连接测试 | 验证数据库连接是否正常     |
| `query_test`      | 查询功能测试 | 执行多个测试查询验证功能   |
| `health_check`    | 健康状态检查 | 检查服务器状态和性能指标   |
| `show_tables`     | 显示表信息   | 获取数据库表列表和详细信息 |
| `stats`           | 统计信息     | 显示测试执行统计数据       |

## 📋 返回结果格式

所有操作都返回统一的 JSON 格式：

```json
{
  "status": "success|error|healthy|unhealthy",
  "message": "操作结果描述",
  "plugin_info": {
    "plugin_name": "mysql_test",
    "operation": "test_connection",
    "timestamp": "2024-01-01T12:00:00",
    "pymysql_available": true
  }
  // ... 具体操作的返回数据
}
```

## 🔍 示例输出

### 连接测试成功

```json
{
  "status": "success",
  "message": "MySQL连接测试成功",
  "connection_time": 0.045,
  "server_info": "8.0.34",
  "host_info": "localhost via TCP/IP",
  "protocol_info": 10,
  "test_query_result": { "test": 1 },
  "config": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "***",
    "database": "test",
    "charset": "utf8mb4"
  }
}
```

### 健康检查结果

```json
{
  "status": "healthy",
  "message": "MySQL服务正常",
  "health_info": {
    "connection": "healthy",
    "server_status": {
      "Threads_connected": "1",
      "Threads_running": "1",
      "Uptime": "3600",
      "Questions": "150"
    },
    "database_size_mb": 15.6
  }
}
```

## 🚨 常见问题

### 1. PyMySQL 未安装

```bash
pip install PyMySQL cryptography
```

### 2. 连接被拒绝

- 检查 MySQL 服务是否启动
- 验证主机名和端口是否正确
- 确认用户名和密码是否正确

### 3. 权限不足

- 确保用户有访问指定数据库的权限
- 检查是否有执行 SHOW 命令的权限

### 4. SSL 连接问题

- 如果不需要 SSL，设置 `MYSQL_SSL_DISABLED=true`
- 如果需要 SSL，提供正确的证书文件路径

## 📝 开发说明

这个插件展示了以下最佳实践：

1. **环境变量配置**: 使用 `.env` 文件管理敏感配置
2. **错误处理**: 完善的异常捕获和错误信息返回
3. **上下文管理**: 使用 `contextmanager` 确保数据库连接正确关闭
4. **统计跟踪**: 记录和报告测试执行统计
5. **灵活操作**: 支持多种测试操作类型
6. **安全考虑**: 在日志中隐藏敏感信息

## 🔗 相关链接

- [PyMySQL 文档](https://pymysql.readthedocs.io/)
- [MySQL 配置参考](https://dev.mysql.com/doc/refman/8.0/en/)
- [插件开发指南](../../README.md)
