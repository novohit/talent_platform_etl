"""
API数据获取器
从REST API获取数据
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils import get_logger, timing, retry, rate_limit
from config import get_config


@dataclass
class APIResponse:
    """API响应数据类"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    url: str


class APIFetcher:
    """API数据获取器"""
    
    def __init__(self):
        self.config = get_config().fetcher
        self.logger = get_logger("api_fetcher")
        self.session_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0
        }
    
    @timing
    @retry(max_attempts=3)
    @rate_limit(calls_per_second=1.0)
    def fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> APIResponse:
        """
        从API获取数据
        
        Args:
            endpoint: API端点
            params: 请求参数
        
        Returns:
            API响应对象
        """
        self.logger.info(f"Fetching data from endpoint: {endpoint}")
        
        # 模拟API请求
        start_time = time.time()
        
        try:
            # 构建完整URL
            full_url = f"{self.config.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # 模拟网络延迟和处理
            time.sleep(0.1)  # 模拟网络延迟
            
            # 模拟不同的响应
            if endpoint == "teachers":
                mock_data = self._generate_mock_teachers_data(params or {})
            elif endpoint == "schools":
                mock_data = self._generate_mock_schools_data(params or {})
            else:
                mock_data = {"message": f"Mock data for {endpoint}"}
            
            response_time = time.time() - start_time
            
            response = APIResponse(
                status_code=200,
                data=mock_data,
                headers={"Content-Type": "application/json"},
                response_time=response_time,
                url=full_url
            )
            
            # 更新统计
            self.session_stats['total_requests'] += 1
            self.session_stats['successful_requests'] += 1
            self.session_stats['total_response_time'] += response_time
            
            self.logger.info(f"Successfully fetched data from {endpoint} in {response_time:.2f}s")
            return response
            
        except Exception as e:
            self.session_stats['total_requests'] += 1
            self.session_stats['failed_requests'] += 1
            self.logger.error(f"Failed to fetch data from {endpoint}: {str(e)}")
            raise
    
    @timing
    def fetch_batch(self, endpoints: List[str], batch_size: int = None) -> List[APIResponse]:
        """
        批量获取数据
        
        Args:
            endpoints: 端点列表
            batch_size: 批次大小
        
        Returns:
            API响应列表
        """
        batch_size = batch_size or self.config.api_retries
        responses = []
        
        self.logger.info(f"Starting batch fetch for {len(endpoints)} endpoints")
        
        for i in range(0, len(endpoints), batch_size):
            batch = endpoints[i:i + batch_size]
            batch_responses = []
            
            for endpoint in batch:
                try:
                    response = self.fetch_data(endpoint)
                    batch_responses.append(response)
                except Exception as e:
                    self.logger.error(f"Failed to fetch {endpoint} in batch: {str(e)}")
                    # 创建错误响应
                    error_response = APIResponse(
                        status_code=500,
                        data={"error": str(e)},
                        headers={},
                        response_time=0.0,
                        url=endpoint
                    )
                    batch_responses.append(error_response)
            
            responses.extend(batch_responses)
            
            # 批次间延迟
            if i + batch_size < len(endpoints):
                time.sleep(0.5)
        
        self.logger.info(f"Completed batch fetch: {len(responses)} responses")
        return responses
    
    def _generate_mock_teachers_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟教师数据"""
        page = params.get('page', 1)
        limit = params.get('limit', 10)
        
        # 模拟分页数据
        total = 150
        start_id = (page - 1) * limit + 1
        
        teachers = []
        for i in range(limit):
            teacher_id = start_id + i
            if teacher_id > total:
                break
                
            teachers.append({
                'id': teacher_id,
                'name': f'Teacher {teacher_id}',
                'email': f'teacher{teacher_id}@example.com',
                'school_id': (teacher_id % 10) + 1,
                'subject': ['Math', 'Science', 'English', 'History'][teacher_id % 4],
                'is_valid': teacher_id % 7 != 0,  # 模拟一些无效数据
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            })
        
        return {
            'data': teachers,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            },
            'metadata': {
                'timestamp': time.time(),
                'source': 'mock_api'
            }
        }
    
    def _generate_mock_schools_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟学校数据"""
        schools = [
            {'id': i, 'name': f'School {i}', 'city': f'City {i%5}', 'type': 'public' if i%2==0 else 'private'}
            for i in range(1, 11)
        ]
        
        return {
            'data': schools,
            'metadata': {
                'timestamp': time.time(),
                'source': 'mock_api'
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        total_requests = self.session_stats['total_requests']
        avg_response_time = (
            self.session_stats['total_response_time'] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.session_stats['successful_requests'],
            'failed_requests': self.session_stats['failed_requests'],
            'success_rate': self.session_stats['successful_requests'] / max(total_requests, 1),
            'average_response_time': avg_response_time,
            'configuration': {
                'base_url': self.config.api_base_url,
                'timeout': self.config.api_timeout,
                'retries': self.config.api_retries,
                'rate_limit': self.config.api_rate_limit
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.fetch_data("health")
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.response_time,
                'api_url': self.config.api_base_url
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'api_url': self.config.api_base_url
            } 