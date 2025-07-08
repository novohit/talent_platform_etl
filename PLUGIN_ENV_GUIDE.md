# 插件环境变量配置指南

## 🌍 概述

插件环境变量功能允许每个插件拥有独立的环境配置，实现更好的配置隔离和灵活性。每个插件可以在其目录下放置 `.env` 文件来定义专属的环境变量。

## 🚀 核心特性

- ✅ **插件级隔离**：每个插件拥有独立的环境变量空间
- ✅ **自动加载**：插件执行时自动设置环境变量
- ✅ **安全恢复**：执行完成后自动恢复原始环境
- ✅ **类型解析**：支持字符串、数字、布尔值、JSON 等类型
- ✅ **热加载支持**：环境配置更新时自动重载

## 📂 插件目录结构

```
plugins/
└── your_plugin/
    ├── plugin.json      # 插件元数据
    ├── main.py          # 插件代码
    ├── .env            # 插件环境配置
    ├── .env.example    # 环境配置示例
    └── requirements.txt # 依赖 (可选)
```

## 🔧 基本使用

### 1. 创建插件环境配置

在插件目录下创建 `.env` 文件：

```bash
# plugins/my_plugin/.env

# 基础配置
PLUGIN_NAME=my_plugin
DEBUG=true
LOG_LEVEL=INFO

# 业务配置
MAX_ITEMS=1000
TIMEOUT=30.0
RETRY_COUNT=3

# 功能开关
CACHE_ENABLED=true
MONITORING_ENABLED=false

# 外部服务
API_BASE_URL=https://api.example.com
API_KEY=your_api_key_here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=my_database
```

### 2. 在插件代码中使用环境变量

```python
import os

def my_plugin_function(**kwargs):
    # 读取环境变量
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    max_items = int(os.getenv('MAX_ITEMS', '100'))
    api_url = os.getenv('API_BASE_URL', 'https://default.api.com')

    if debug:
        print(f"Debug mode enabled, max_items: {max_items}")

    # 使用配置进行业务逻辑
    # ...
```

### 3. 测试插件

```bash
# 测试插件 (会自动加载环境变量)
python -m talent_platform.scheduler_app test-plugin my_plugin
```

## 📋 支持的数据类型

### 字符串类型

```bash
PLUGIN_NAME=my_plugin
API_BASE_URL=https://api.example.com
```

```python
plugin_name = os.getenv('PLUGIN_NAME', 'default')
api_url = os.getenv('API_BASE_URL', 'https://default.com')
```

### 数字类型

```bash
MAX_ITEMS=1000
TIMEOUT=30.5
```

```python
max_items = int(os.getenv('MAX_ITEMS', '100'))
timeout = float(os.getenv('TIMEOUT', '30.0'))
```

### 布尔类型

```bash
DEBUG=true
CACHE_ENABLED=false
MONITORING_ENABLED=1
SSL_VERIFY=yes
```

```python
def parse_bool(value, default=False):
    if not value:
        return default
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

debug = parse_bool(os.getenv('DEBUG'))
cache_enabled = parse_bool(os.getenv('CACHE_ENABLED'))
```

### 列表类型

```bash
FEATURES_ENABLED=basic,advanced,premium
ALLOWED_HOSTS=localhost,127.0.0.1,example.com
```

```python
features = os.getenv('FEATURES_ENABLED', '').split(',')
hosts = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
```

### JSON 类型

```bash
CUSTOM_SETTINGS={"theme": "dark", "language": "zh-CN"}
MAPPING_RULES={"user_id": "id", "user_name": "name"}
```

```python
import json

try:
    settings = json.loads(os.getenv('CUSTOM_SETTINGS', '{}'))
    mapping = json.loads(os.getenv('MAPPING_RULES', '{}'))
except json.JSONDecodeError:
    settings = {}
    mapping = {}
```

## 🛠️ 高级功能

### 1. 环境配置管理类

创建一个配置管理类来统一处理环境变量：

```python
import os
import json
import logging

logger = logging.getLogger(__name__)

class PluginConfig:
    def __init__(self):
        # 基础配置
        self.plugin_name = os.getenv('PLUGIN_NAME', 'unknown')
        self.debug = self._parse_bool('DEBUG', False)
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # 业务配置
        self.max_items = self._parse_int('MAX_ITEMS', 1000)
        self.timeout = self._parse_float('TIMEOUT', 30.0)
        self.retry_count = self._parse_int('RETRY_COUNT', 3)

        # 功能开关
        self.cache_enabled = self._parse_bool('CACHE_ENABLED', True)
        self.monitoring = self._parse_bool('MONITORING_ENABLED', False)

        # 外部服务
        self.api_url = os.getenv('API_BASE_URL', 'https://api.example.com')
        self.api_key = os.getenv('API_KEY', '')

        # 高级配置
        self.custom_settings = self._parse_json('CUSTOM_SETTINGS', {})

        if self.debug:
            logger.info(f"Configuration loaded for {self.plugin_name}")

    def _parse_bool(self, key, default=False):
        value = os.getenv(key, '').lower()
        return value in ('true', '1', 'yes', 'on', 'enabled') if value else default

    def _parse_int(self, key, default=0):
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer for {key}, using default: {default}")
            return default

    def _parse_float(self, key, default=0.0):
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float for {key}, using default: {default}")
            return default

    def _parse_json(self, key, default=None):
        try:
            value = os.getenv(key, '{}')
            return json.loads(value) if value else (default or {})
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON for {key}: {e}, using default")
            return default or {}

# 使用配置类
def my_plugin_function(**kwargs):
    config = PluginConfig()

    if config.debug:
        logger.debug(f"Processing with config: {config.plugin_name}")

    # 使用配置
    # ...
```

### 2. 配置验证

```python
class PluginConfig:
    def __init__(self):
        # ... 配置加载 ...
        self._validate_config()

    def _validate_config(self):
        """验证配置有效性"""
        errors = []

        if not self.api_key:
            errors.append("API_KEY is required")

        if self.timeout <= 0:
            errors.append("TIMEOUT must be positive")

        if self.max_items <= 0:
            errors.append("MAX_ITEMS must be positive")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
```

### 3. 环境特定配置

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
API_BASE_URL=https://dev-api.example.com

# .env.production
DEBUG=false
LOG_LEVEL=WARNING
API_BASE_URL=https://api.example.com
```

## 📝 实际示例

### 示例 1：数据处理插件

```bash
# plugins/data_processor/.env
PLUGIN_NAME=data_processor
DEBUG=false
BATCH_SIZE=1000
MAX_WORKERS=4
CACHE_TTL=3600
DATABASE_URL=mysql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
```

```python
# plugins/data_processor/main.py
import os
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

def process_data(operation: str, **kwargs):
    # 读取配置
    batch_size = int(os.getenv('BATCH_SIZE', '100'))
    max_workers = int(os.getenv('MAX_WORKERS', '2'))
    cache_ttl = int(os.getenv('CACHE_TTL', '1800'))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    if debug:
        logger.debug(f"Processing with batch_size={batch_size}, workers={max_workers}")

    # 使用线程池处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 批量处理逻辑
        pass

    return {"status": "success", "batch_size": batch_size}
```

### 示例 2：API 集成插件

```bash
# plugins/api_client/.env
API_BASE_URL=https://api.service.com
API_KEY=sk-1234567890
API_VERSION=v2
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT=100
SSL_VERIFY=true
USER_AGENT=MyPlugin/1.0
```

```python
# plugins/api_client/main.py
import os
import requests
import time

def api_call(endpoint: str, **kwargs):
    # API配置
    base_url = os.getenv('API_BASE_URL')
    api_key = os.getenv('API_KEY')
    version = os.getenv('API_VERSION', 'v1')
    timeout = float(os.getenv('REQUEST_TIMEOUT', '30'))
    max_retries = int(os.getenv('MAX_RETRIES', '3'))
    ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
    user_agent = os.getenv('USER_AGENT', 'Plugin/1.0')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': user_agent,
        'Content-Type': 'application/json'
    }

    url = f"{base_url}/{version}/{endpoint}"

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=ssl_verify
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

## 🔒 安全最佳实践

### 1. 敏感信息处理

```bash
# 使用安全的方式存储敏感信息
API_KEY=your_api_key_here
DB_PASSWORD=secure_password
ENCRYPTION_KEY=your_encryption_key

# 不要在代码中硬编码敏感信息
```

### 2. 环境变量验证

```python
def validate_security_config():
    api_key = os.getenv('API_KEY')
    if not api_key or len(api_key) < 10:
        raise ValueError("API_KEY must be at least 10 characters")

    if api_key == 'your_api_key_here':
        raise ValueError("Please set a real API_KEY")
```

### 3. 日志安全

```python
import logging

def safe_log_config():
    config = {
        'api_url': os.getenv('API_BASE_URL'),
        'timeout': os.getenv('TIMEOUT'),
        'has_api_key': bool(os.getenv('API_KEY')),  # 不记录实际密钥
        'ssl_verify': os.getenv('SSL_VERIFY')
    }

    logging.info(f"Plugin configuration: {config}")
```

## ⚡ 性能优化

### 1. 配置缓存

```python
class CachedConfig:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls):
        return {
            'timeout': float(os.getenv('TIMEOUT', '30')),
            'max_items': int(os.getenv('MAX_ITEMS', '1000')),
            # ... 其他配置
        }

    def get(self, key, default=None):
        return self._config.get(key, default)
```

### 2. 延迟加载

```python
class LazyConfig:
    def __init__(self):
        self._cache = {}

    def get_timeout(self):
        if 'timeout' not in self._cache:
            self._cache['timeout'] = float(os.getenv('TIMEOUT', '30'))
        return self._cache['timeout']
```

## 🐛 故障排除

### 常见问题

**1. 环境变量未生效**

```bash
# 检查 .env 文件是否存在
ls -la plugins/your_plugin/.env

# 检查文件内容
cat plugins/your_plugin/.env

# 测试插件并查看日志
python -m talent_platform.scheduler_app test-plugin your_plugin
```

**2. 类型转换错误**

```python
# 添加异常处理
try:
    max_items = int(os.getenv('MAX_ITEMS', '100'))
except ValueError:
    logger.error(f"Invalid MAX_ITEMS value: {os.getenv('MAX_ITEMS')}")
    max_items = 100
```

**3. 配置冲突**

```python
# 打印实际使用的配置
config_info = {
    key: os.getenv(key, 'NOT_SET')
    for key in ['API_KEY', 'DB_HOST', 'TIMEOUT']
}
logger.info(f"Current environment config: {config_info}")
```

## 📚 示例插件参考

系统提供了两个示例插件：

1. **hot_reload_demo**: 展示基础环境变量使用
2. **env_demo**: 展示完整的环境配置管理

```bash
# 查看示例
ls -la plugins/*/config.env.example

# 测试示例插件
python -m talent_platform.scheduler_app test-plugin env_demo --operation demo
```

---

**相关文档：**

- 🔥 [热加载功能指南](HOT_RELOAD_GUIDE.md)
- 📋 [系统使用指南](SCHEDULER_USAGE.md)
- 🏗️ [系统设计文档](SCHEDULER_SUMMARY.md)
