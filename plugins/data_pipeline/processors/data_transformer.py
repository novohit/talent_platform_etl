"""
数据转换器
提供数据转换和格式化功能
"""

from typing import Dict, List, Any
from utils import get_logger, timing


class DataTransformer:
    """数据转换器"""
    
    def __init__(self):
        self.logger = get_logger("data_transformer")
    
    @timing
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换数据"""
        self.logger.info(f"Transforming {len(data)} records")
        
        transformed_data = []
        for record in data:
            transformed_record = self._transform_record(record)
            transformed_data.append(transformed_record)
        
        self.logger.info(f"Transformed {len(transformed_data)} records")
        return transformed_data
    
    def _transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """转换单条记录"""
        transformed = record.copy()
        
        # 添加转换时间戳
        from datetime import datetime
        transformed['transformed_at'] = datetime.now().isoformat()
        
        return transformed 