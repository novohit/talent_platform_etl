"""
数据库数据获取器
从数据库获取数据
"""

from typing import Dict, List, Any
from ..utils import get_logger, timing


class DatabaseFetcher:
    """数据库数据获取器"""
    
    def __init__(self):
        self.logger = get_logger("database_fetcher")
    
    @timing
    def fetch(self, table: str, limit: int = 100) -> List[Dict[str, Any]]:
        """从数据库获取数据"""
        self.logger.info(f"Fetching data from table: {table}")
        
        # 模拟数据库查询
        mock_data = [
            {'id': i, 'name': f'DB Record {i}', 'table': table}
            for i in range(1, limit + 1)
        ]
        
        self.logger.info(f"Fetched {len(mock_data)} records from {table}")
        return mock_data 