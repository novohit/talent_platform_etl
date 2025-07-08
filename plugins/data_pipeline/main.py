"""
数据管道插件主入口
提供完整的ETL数据处理管道功能
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入各个功能包
from .utils import get_logger, timing, Timer, format_duration, format_size
from .config import get_config, get_config_summary, validate_configuration
from .fetchers import APIFetcher


class DataPipeline:
    """数据处理管道主类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("data_pipeline")
        self.pipeline_stats = {
            'executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'records_processed': 0,
            'last_execution': None
        }
        
        # 初始化各个组件
        self.api_fetcher = APIFetcher()
        
        self.logger.info(f"Data pipeline initialized: {self.config.plugin_name}")
    
    @timing
    def run_pipeline(self, 
                    operation: str = "full_pipeline",
                    source: str = "api",
                    **kwargs) -> Dict[str, Any]:
        """
        运行数据管道
        
        Args:
            operation: 操作类型 (full_pipeline, fetch_only, process_only, etc.)
            source: 数据源类型 (api, database, file)
            **kwargs: 其他参数
        
        Returns:
            执行结果字典
        """
        execution_id = f"exec_{int(time.time())}"
        
        self.logger.info(f"Starting pipeline execution {execution_id}")
        self.logger.info(f"Operation: {operation}, Source: {source}")
        
        with Timer("Pipeline execution") as timer:
            try:
                # 更新统计
                self.pipeline_stats['executions'] += 1
                self.pipeline_stats['last_execution'] = datetime.now()
                
                # 配置验证
                config_validation = validate_configuration()
                if not config_validation['valid']:
                    raise ValueError(f"Configuration validation failed: {config_validation['errors']}")
                
                # 根据操作类型执行不同的流程
                if operation == "full_pipeline":
                    result = self._run_full_pipeline(source, **kwargs)
                elif operation == "fetch_only":
                    result = self._run_fetch_only(source, **kwargs)
                elif operation == "health_check":
                    result = self._run_health_check(**kwargs)
                elif operation == "config_info":
                    result = self._get_config_info(**kwargs)
                elif operation == "stats":
                    result = self._get_pipeline_stats(**kwargs)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                # 更新成功统计
                self.pipeline_stats['successful_executions'] += 1
                self.pipeline_stats['total_execution_time'] += timer.elapsed
                self.pipeline_stats['records_processed'] += result.get('records_processed', 0)
                
                # 添加执行信息到结果
                result['execution_info'] = {
                    'execution_id': execution_id,
                    'operation': operation,
                    'source': source,
                    'execution_time': timer.elapsed,
                    'execution_time_formatted': timer.elapsed_str,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                
                self.logger.info(f"Pipeline execution {execution_id} completed successfully in {timer.elapsed_str}")
                return result
                
            except Exception as e:
                # 更新失败统计
                self.pipeline_stats['failed_executions'] += 1
                self.pipeline_stats['total_execution_time'] += timer.elapsed
                
                error_result = {
                    'status': 'error',
                    'error': str(e),
                    'execution_info': {
                        'execution_id': execution_id,
                        'operation': operation,
                        'source': source,
                        'execution_time': timer.elapsed,
                        'execution_time_formatted': timer.elapsed_str,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'failed'
                    }
                }
                
                self.logger.error(f"Pipeline execution {execution_id} failed: {str(e)}")
                raise
    
    def _run_full_pipeline(self, source: str, **kwargs) -> Dict[str, Any]:
        """运行完整的数据管道"""
        self.logger.info("Running full data pipeline")
        
        # 1. 数据获取阶段
        fetch_result = self._run_fetch_only(source, **kwargs)
        raw_data = fetch_result['data']
        
        # 2. 数据处理阶段
        processed_data = self._process_data(raw_data, **kwargs)
        
        # 3. 数据存储阶段
        storage_result = self._store_data(processed_data, **kwargs)
        
        return {
            'status': 'success',
            'pipeline_type': 'full',
            'stages_completed': ['fetch', 'process', 'store'],
            'records_fetched': len(raw_data),
            'records_processed': len(processed_data),
            'records_stored': storage_result['records_stored'],
            'data_sample': processed_data[:3] if processed_data else [],
            'fetch_stats': fetch_result.get('stats'),
            'storage_stats': storage_result
        }
    
    def _run_fetch_only(self, source: str, **kwargs) -> Dict[str, Any]:
        """仅运行数据获取"""
        self.logger.info(f"Running data fetch from source: {source}")
        
        if source == "api":
            return self._fetch_from_api(**kwargs)
        elif source == "database":
            return self._fetch_from_database(**kwargs)
        elif source == "file":
            return self._fetch_from_file(**kwargs)
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def _fetch_from_api(self, **kwargs) -> Dict[str, Any]:
        """从API获取数据"""
        endpoint = kwargs.get('endpoint', 'teachers')
        params = kwargs.get('params', {})
        batch_mode = kwargs.get('batch_mode', False)
        
        self.logger.info(f"Fetching data from API endpoint: {endpoint}")
        
        if batch_mode:
            endpoints = kwargs.get('endpoints', [endpoint])
            responses = self.api_fetcher.fetch_batch(endpoints)
            data = []
            for response in responses:
                if response.status_code == 200:
                    if 'data' in response.data:
                        data.extend(response.data['data'])
                    else:
                        data.append(response.data)
        else:
            response = self.api_fetcher.fetch_data(endpoint, params)
            if response.status_code == 200:
                data = response.data.get('data', [response.data])
            else:
                data = []
        
        return {
            'status': 'success',
            'source': 'api',
            'data': data,
            'records_count': len(data),
            'stats': self.api_fetcher.get_stats()
        }
    
    def _fetch_from_database(self, **kwargs) -> Dict[str, Any]:
        """从数据库获取数据"""
        # 模拟数据库获取
        self.logger.info("Fetching data from database (simulated)")
        
        table = kwargs.get('table', 'teachers')
        limit = kwargs.get('limit', 50)
        
        # 模拟数据库数据
        mock_data = [
            {
                'id': i,
                'name': f'DB Teacher {i}',
                'email': f'dbteacher{i}@example.com',
                'department': ['Math', 'Science', 'English'][i % 3],
                'salary': 50000 + (i * 1000),
                'hire_date': '2024-01-01',
                'is_active': i % 5 != 0
            }
            for i in range(1, limit + 1)
        ]
        
        return {
            'status': 'success',
            'source': 'database',
            'data': mock_data,
            'records_count': len(mock_data),
            'table': table
        }
    
    def _fetch_from_file(self, **kwargs) -> Dict[str, Any]:
        """从文件获取数据"""
        # 模拟文件获取
        self.logger.info("Fetching data from file (simulated)")
        
        file_path = kwargs.get('file_path', 'teachers.csv')
        file_format = kwargs.get('format', 'csv')
        
        # 模拟文件数据
        mock_data = [
            {
                'id': i,
                'name': f'File Teacher {i}',
                'subject': ['Physics', 'Chemistry', 'Biology'][i % 3],
                'experience_years': i % 20,
                'certification': i % 3 == 0
            }
            for i in range(1, 26)
        ]
        
        return {
            'status': 'success',
            'source': 'file',
            'data': mock_data,
            'records_count': len(mock_data),
            'file_path': file_path,
            'file_format': file_format
        }
    
    def _process_data(self, raw_data: List[Dict], **kwargs) -> List[Dict]:
        """处理数据"""
        self.logger.info(f"Processing {len(raw_data)} records")
        
        processed_data = []
        config = self.config.processor
        
        for record in raw_data:
            try:
                # 基本数据清洗
                cleaned_record = self._clean_record(record)
                
                # 数据验证
                if self._validate_record(cleaned_record):
                    # 数据转换
                    transformed_record = self._transform_record(cleaned_record)
                    processed_data.append(transformed_record)
                else:
                    self.logger.warning(f"Record validation failed: {record.get('id', 'unknown')}")
                    
            except Exception as e:
                self.logger.error(f"Error processing record {record.get('id', 'unknown')}: {str(e)}")
                if not config.continue_on_error:
                    raise
        
        self.logger.info(f"Successfully processed {len(processed_data)} records")
        return processed_data
    
    def _clean_record(self, record: Dict) -> Dict:
        """清洗单条记录"""
        cleaned = record.copy()
        
        # 移除空值字段
        cleaned = {k: v for k, v in cleaned.items() if v is not None}
        
        # 标准化文本字段
        for field in ['name', 'email']:
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned[field] = cleaned[field].strip()
        
        # 添加处理时间戳
        cleaned['processed_at'] = datetime.now().isoformat()
        
        return cleaned
    
    def _validate_record(self, record: Dict) -> bool:
        """验证单条记录"""
        # 基本验证规则
        required_fields = ['id', 'name']
        
        for field in required_fields:
            if field not in record or not record[field]:
                return False
        
        # 邮箱格式验证
        if 'email' in record:
            email = record['email']
            if '@' not in email or '.' not in email:
                return False
        
        return True
    
    def _transform_record(self, record: Dict) -> Dict:
        """转换单条记录"""
        transformed = record.copy()
        
        # 添加计算字段
        if 'name' in transformed:
            transformed['name_length'] = len(transformed['name'])
        
        # 标准化布尔字段
        bool_fields = ['is_valid', 'is_active', 'certification']
        for field in bool_fields:
            if field in transformed:
                transformed[field] = bool(transformed[field])
        
        # 添加转换标记
        transformed['transformation_version'] = '1.0'
        
        return transformed
    
    def _store_data(self, processed_data: List[Dict], **kwargs) -> Dict[str, Any]:
        """存储数据"""
        self.logger.info(f"Storing {len(processed_data)} records")
        
        storage_type = kwargs.get('storage_type', 'database')
        
        # 模拟存储操作
        time.sleep(0.2)  # 模拟存储延迟
        
        return {
            'records_stored': len(processed_data),
            'storage_type': storage_type,
            'storage_time': 0.2,
            'success': True
        }
    
    def _run_health_check(self, **kwargs) -> Dict[str, Any]:
        """运行健康检查"""
        self.logger.info("Running pipeline health check")
        
        health_results = {
            'pipeline_status': 'healthy',
            'components': {},
            'configuration': {},
            'statistics': {}
        }
        
        # API健康检查
        api_health = self.api_fetcher.health_check()
        health_results['components']['api_fetcher'] = api_health
        
        # 配置验证
        config_validation = validate_configuration()
        health_results['configuration'] = config_validation
        
        # 统计信息
        health_results['statistics'] = self.pipeline_stats.copy()
        
        # 总体状态判断
        if (api_health['status'] != 'healthy' or 
            not config_validation['valid']):
            health_results['pipeline_status'] = 'unhealthy'
        
        return health_results
    
    def _get_config_info(self, **kwargs) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'config_summary': get_config_summary(),
            'config_validation': validate_configuration(),
            'environment_variables': {
                'LOG_LEVEL': self.config.pipeline.log_level,
                'BATCH_SIZE': self.config.processor.batch_size,
                'API_BASE_URL': self.config.fetcher.api_base_url,
                'EXECUTION_MODE': self.config.pipeline.execution_mode
            }
        }
    
    def _get_pipeline_stats(self, **kwargs) -> Dict[str, Any]:
        """获取管道统计信息"""
        stats = self.pipeline_stats.copy()
        
        # 计算派生统计
        if stats['executions'] > 0:
            stats['success_rate'] = stats['successful_executions'] / stats['executions']
            stats['average_execution_time'] = stats['total_execution_time'] / stats['executions']
            stats['average_records_per_execution'] = stats['records_processed'] / stats['executions']
        else:
            stats['success_rate'] = 0
            stats['average_execution_time'] = 0
            stats['average_records_per_execution'] = 0
        
        # 添加格式化信息
        stats['total_execution_time_formatted'] = format_duration(stats['total_execution_time'])
        stats['average_execution_time_formatted'] = format_duration(stats['average_execution_time'])
        
        return stats


# 主入口函数
def run_data_pipeline(operation: str = "full_pipeline", 
                     source: str = "api", 
                     **kwargs) -> Dict[str, Any]:
    """
    数据管道插件主入口函数
    
    Args:
        operation: 操作类型
        source: 数据源
        **kwargs: 其他参数
    
    Returns:
        执行结果
    """
    print(f"run_data_pipelineBBBBBB====")
    pipeline = DataPipeline()
    return pipeline.run_pipeline(operation, source, **kwargs)


# 兼容性别名
process_data = run_data_pipeline 