"""
文件数据获取器
从文件获取数据
"""

from typing import Dict, List, Any
from ..utils import get_logger, timing


class FileFetcher:
    """文件数据获取器"""
    
    def __init__(self):
        self.logger = get_logger("file_fetcher")
    
    @timing
    def fetch(self, file_path: str, format: str = 'csv') -> List[Dict[str, Any]]:
        """从文件获取数据"""
        self.logger.info(f"Fetching data from file: {file_path}")
        
        # 模拟文件读取
        mock_data = [
            {'id': i, 'name': f'File Record {i}', 'source_file': file_path}
            for i in range(1, 26)
        ]
        
        self.logger.info(f"Fetched {len(mock_data)} records from {file_path}")
        return mock_data 