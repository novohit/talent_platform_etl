"""
数据验证器
提供数据验证和质量检查功能
"""

from typing import Dict, List, Any, Tuple
from ..utils import get_logger, timing


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.logger = get_logger("data_validator")
    
    @timing
    def validate(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """验证数据，返回(有效数据, 无效数据)"""
        self.logger.info(f"Validating {len(data)} records")
        
        valid_data = []
        invalid_data = []
        
        for record in data:
            if self._validate_record(record):
                valid_data.append(record)
            else:
                invalid_data.append(record)
        
        self.logger.info(f"Validation completed: {len(valid_data)} valid, {len(invalid_data)} invalid")
        return valid_data, invalid_data
    
    def _validate_record(self, record: Dict[str, Any]) -> bool:
        """验证单条记录"""
        # 基本验证规则
        if not record.get('id'):
            return False
        
        if not record.get('name'):
            return False
        
        return True 