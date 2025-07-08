"""
数据清洗器
提供数据清洗和标准化功能
"""

from typing import Dict, List, Any
from utils import get_logger, timing


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.logger = get_logger("data_cleaner")
    
    @timing
    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗数据"""
        self.logger.info(f"Cleaning {len(data)} records")
        
        cleaned_data = []
        for record in data:
            cleaned_record = self._clean_record(record)
            if cleaned_record:
                cleaned_data.append(cleaned_record)
        
        self.logger.info(f"Cleaned {len(cleaned_data)} records")
        return cleaned_data
    
    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单条记录"""
        cleaned = {}
        
        for key, value in record.items():
            # 清理字符串
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value
        
        return cleaned 