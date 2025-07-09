#!/usr/bin/env python3
"""
MySQL连接测试插件
提供MySQL数据库连接测试和基本操作验证功能
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False
    pymysql = None


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class MySQLTester:
    """MySQL测试器"""
    
    def __init__(self):
        if not HAS_PYMYSQL:
            raise ImportError("PyMySQL is not installed. Please install it using: pip install PyMySQL")
        
        self.config = MySQLConfig()
        self.connection_pool = []
        self.test_stats = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'last_test_time': None,
            'last_error': None
        }
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        connection = None
        try:
            connection_params = self.config.get_connection_params()
            connection = pymysql.connect(**connection_params)
            logger.info(f"Successfully connected to MySQL: {self.config.host}:{self.config.port}")
            yield connection
            
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise
            
        finally:
            if connection:
                connection.close()
                logger.debug("MySQL connection closed")
    
    def test_connection(self, timeout: int = 30) -> Dict[str, Any]:
        """测试基本连接"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                # 执行简单查询验证连接
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                
                connection_time = time.time() - start_time
                
                self.test_stats['total_tests'] += 1
                self.test_stats['successful_tests'] += 1
                self.test_stats['last_test_time'] = datetime.now()
                
                return {
                    'status': 'success',
                    'message': 'MySQL连接测试成功',
                    'connection_time': round(connection_time, 3),
                    'server_info': conn.get_server_info(),
                    'host_info': conn.get_host_info(),
                    'protocol_info': conn.get_proto_info(),
                    'test_query_result': result,
                    'config': self.config.to_dict()
                }
                
        except Exception as e:
            self.test_stats['total_tests'] += 1
            self.test_stats['failed_tests'] += 1
            self.test_stats['last_error'] = str(e)
            self.test_stats['last_test_time'] = datetime.now()
            
            return {
                'status': 'error',
                'message': f'MySQL连接测试失败: {str(e)}',
                'connection_time': round(time.time() - start_time, 3),
                'error_type': type(e).__name__,
                'config': self.config.to_dict()
            }
    
    def query_test(self, **kwargs) -> Dict[str, Any]:
        """执行查询测试"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 测试查询
                    test_queries = [
                        ("SELECT VERSION() as version", "获取MySQL版本"),
                        ("SELECT NOW() as current_time", "获取当前时间"),
                        ("SELECT DATABASE() as current_db", "获取当前数据库"),
                        ("SELECT USER() as current_user", "获取当前用户"),
                        ("SHOW STATUS LIKE 'Uptime'", "获取服务器运行时间"),
                        ("SELECT @@sql_mode as sql_mode", "获取SQL模式")
                    ]
                    
                    results = []
                    total_time = 0
                    
                    for query, description in test_queries:
                        start_time = time.time()
                        try:
                            cursor.execute(query)
                            result = cursor.fetchall()
                            query_time = time.time() - start_time
                            total_time += query_time
                            
                            logger.info(f"query: {query}")
                            logger.info(f"result: {result}")
                            results.append({
                                'query': query,
                                'description': description,
                                'status': 'success',
                                'result': result,
                                'execution_time': round(query_time, 4)
                            })
                            
                        except Exception as e:
                            results.append({
                                'query': query,
                                'description': description,
                                'status': 'error',
                                'error': str(e),
                                'execution_time': round(time.time() - start_time, 4)
                            })
                    
                    return {
                        'status': 'success',
                        'message': f'执行了{len(test_queries)}个测试查询',
                        'total_execution_time': round(total_time, 4),
                        'queries': results
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'message': f'查询测试失败: {str(e)}',
                'error_type': type(e).__name__
            }
    
    def show_tables(self, **kwargs) -> Dict[str, Any]:
        """显示数据库表"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取所有表
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    
                    table_details = []
                    
                    # 获取每个表的详细信息
                    for table_row in tables:
                        table_name = list(table_row.values())[0]
                        
                        # 获取表信息
                        cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
                        table_status = cursor.fetchone()
                        
                        # 获取表结构
                        cursor.execute(f"DESCRIBE {table_name}")
                        table_structure = cursor.fetchall()
                        
                        table_details.append({
                            'table_name': table_name,
                            'engine': table_status.get('Engine'),
                            'rows': table_status.get('Rows'),
                            'data_length': table_status.get('Data_length'),
                            'index_length': table_status.get('Index_length'),
                            'create_time': str(table_status.get('Create_time', '')),
                            'update_time': str(table_status.get('Update_time', '')),
                            'columns_count': len(table_structure),
                            'columns': table_structure[:5]  # 只显示前5列
                        })
                    
                    return {
                        'status': 'success',
                        'message': f'数据库 {self.config.database} 包含 {len(tables)} 个表',
                        'database': self.config.database,
                        'tables_count': len(tables),
                        'tables': table_details
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'message': f'获取表列表失败: {str(e)}',
                'error_type': type(e).__name__
            }
    
    def health_check(self, **kwargs) -> Dict[str, Any]:
        """健康检查"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    health_info = {}
                    
                    # 基本连接检查
                    cursor.execute("SELECT 1")
                    health_info['connection'] = 'healthy'
                    
                    # 服务器状态
                    cursor.execute("SHOW STATUS WHERE Variable_name IN ('Threads_connected', 'Threads_running', 'Uptime', 'Questions')")
                    status_vars = {row['Variable_name']: row['Value'] for row in cursor.fetchall()}
                    health_info['server_status'] = status_vars
                    
                    # 数据库大小
                    cursor.execute(f"""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
                        FROM information_schema.tables 
                        WHERE table_schema = '{self.config.database}'
                    """)
                    db_size = cursor.fetchone()
                    health_info['database_size_mb'] = db_size.get('DB Size in MB', 0)
                    
                    # 测试统计
                    health_info['test_statistics'] = self.test_stats
                    
                    return {
                        'status': 'healthy',
                        'message': 'MySQL服务正常',
                        'timestamp': datetime.now().isoformat(),
                        'health_info': health_info
                    }
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'健康检查失败: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'error_type': type(e).__name__,
                'test_statistics': self.test_stats
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        stats = self.test_stats.copy()
        
        if stats['total_tests'] > 0:
            stats['success_rate'] = round(stats['successful_tests'] / stats['total_tests'], 2)
        else:
            stats['success_rate'] = 0
        
        stats['last_test_time_str'] = stats['last_test_time'].isoformat() if stats['last_test_time'] else None
        
        return stats


def test_mysql_connection(operation: str = "query_test", timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """
    MySQL连接测试插件主入口函数
    
    Args:
        operation: 操作类型 (test_connection, query_test, health_check, show_tables)
        timeout: 连接超时时间
        **kwargs: 其他参数
    
    Returns:
        测试结果字典
    """
    logger.info(f"MySQL测试插件启动 - 操作: {operation}")
    
    try:
        tester = MySQLTester()
        
        if operation == "test_connection":
            result = tester.test_connection(timeout)
        elif operation == "query_test":
            result = tester.query_test(**kwargs)
        elif operation == "health_check":
            result = tester.health_check(**kwargs)
        elif operation == "show_tables":
            result = tester.show_tables(**kwargs)
        elif operation == "stats":
            result = {
                'status': 'success',
                'message': '测试统计信息',
                'stats': tester.get_stats()
            }
        else:
            result = {
                'status': 'error',
                'message': f'未知操作类型: {operation}',
                'available_operations': ['test_connection', 'query_test', 'health_check', 'show_tables', 'stats']
            }
        
        # 添加执行信息
        result['plugin_info'] = {
            'plugin_name': 'mysql_test',
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'pymysql_available': HAS_PYMYSQL
        }
        
        logger.info(f"MySQL测试完成 - 状态: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"MySQL测试插件执行失败: {e}")
        return {
            'status': 'error',
            'message': f'插件执行失败: {str(e)}',
            'error_type': type(e).__name__,
            'plugin_info': {
                'plugin_name': 'mysql_test',
                'operation': operation,
                'timestamp': datetime.now().isoformat(),
                'pymysql_available': HAS_PYMYSQL
            }
        }


if __name__ == "__main__":
    # 直接运行时的默认测试
    print("MySQL连接测试插件")
    print("=" * 50)
    
    result = test_mysql_connection("test_connection")
    
    if result['status'] == 'success':
        print("✅ 连接测试成功!")
        print(f"连接时间: {result['connection_time']}秒")
        print(f"服务器版本: {result['server_info']}")
        print(f"主机信息: {result['host_info']}")
    else:
        print("❌ 连接测试失败!")
        print(f"错误信息: {result['message']}")
    
    print("\n配置信息:")
    config = result.get('config', {})
    for key, value in config.items():
        print(f"  {key}: {value}") 