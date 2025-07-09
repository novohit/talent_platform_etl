import os
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
from typing import Dict, Any
from contextlib import contextmanager

try:
    import pymysql
    import pymysql.cursors
    from pymysql.connections import Connection
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False
    pymysql = None


class MySQLConfig:
    """MySQL配置管理"""
    
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.port = int(os.getenv('MYSQL_PORT', '3306'))
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.database = os.getenv('MYSQL_DATABASE', 'test')
        self.charset = os.getenv('MYSQL_CHARSET', 'utf8mb4')
        
        # 连接配置
        self.max_connections = int(os.getenv('MYSQL_MAX_CONNECTIONS', '10'))
        self.connection_timeout = int(os.getenv('MYSQL_CONNECTION_TIMEOUT', '30'))
        self.read_timeout = int(os.getenv('MYSQL_READ_TIMEOUT', '30'))
        self.write_timeout = int(os.getenv('MYSQL_WRITE_TIMEOUT', '30'))
        
        # SSL配置
        self.ssl_disabled = os.getenv('MYSQL_SSL_DISABLED', 'true').lower() == 'true'
        self.ssl_ca = os.getenv('MYSQL_SSL_CA', '')
        self.ssl_cert = os.getenv('MYSQL_SSL_CERT', '')
        self.ssl_key = os.getenv('MYSQL_SSL_KEY', '')
        
        # 其他配置
        self.autocommit = os.getenv('MYSQL_AUTOCOMMIT', 'true').lower() == 'true'
        self.use_unicode = os.getenv('MYSQL_USE_UNICODE', 'true').lower() == 'true'
    
    def get_connection_params(self) -> Dict[str, Any]:
        """获取连接参数"""
        params = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'connect_timeout': self.connection_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout,
            'autocommit': self.autocommit,
            'use_unicode': self.use_unicode,
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        # SSL配置
        if not self.ssl_disabled:
            ssl_config = {}
            if self.ssl_ca:
                ssl_config['ca'] = self.ssl_ca
            if self.ssl_cert:
                ssl_config['cert'] = self.ssl_cert
            if self.ssl_key:
                ssl_config['key'] = self.ssl_key
            
            if ssl_config:
                params['ssl'] = ssl_config
        
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': '***' if self.password else '',
            'database': self.database,
            'charset': self.charset,
            'connection_timeout': self.connection_timeout,
            'ssl_disabled': self.ssl_disabled,
            'autocommit': self.autocommit
        }

_config = MySQLConfig()


@contextmanager
def get_connection() -> Connection:
    """获取数据库连接（上下文管理器）"""
    connection = None
    try:
        connection_params = _config.get_connection_params()
        connection = pymysql.connect(**connection_params)
        logger.info(f"Successfully connected to MySQL: {_config.host}:{_config.port}")
        yield connection
        
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        raise
        
    finally:
        if connection:
            connection.close()
            logger.debug("MySQL connection closed")
