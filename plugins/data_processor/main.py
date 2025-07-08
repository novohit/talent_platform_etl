"""
数据处理插件示例
处理爬虫数据和教师信息
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional


# 配置日志
logger = logging.getLogger(__name__)


def process_data(operation: str = "sync_data", 
                teacher_id: Optional[str] = None,
                data: Optional[Dict] = None,
                sync_type: str = "manual",
                change_event: Optional[Dict] = None,
                **kwargs) -> Dict[str, Any]:
    """
    数据处理主函数
    
    Args:
        operation: 操作类型
        teacher_id: 教师ID
        data: 数据对象
        sync_type: 同步类型
        change_event: 数据库变更事件
        **kwargs: 其他参数
    
    Returns:
        处理结果字典
    """
    
    logger.info(f"Starting data processing: operation={operation}, teacher_id={teacher_id}")
    
    try:
        if operation == "process_new_teacher":
            return _process_new_teacher(teacher_id, data)
        elif operation == "update_teacher_data":
            return _update_teacher_data(teacher_id, data)
        elif operation == "sync_data":
            return _sync_data(sync_type)
        elif operation == "handle_change_event":
            return _handle_change_event(change_event)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def _process_new_teacher(teacher_id: str, data: Optional[Dict]) -> Dict[str, Any]:
    """处理新教师数据"""
    logger.info(f"Processing new teacher: {teacher_id}")
    
    # 模拟数据处理逻辑
    processed_data = {
        "teacher_id": teacher_id,
        "processed_at": datetime.now().isoformat(),
        "processing_steps": [
            "validate_teacher_data",
            "extract_research_fields",
            "normalize_name_format",
            "calculate_metrics"
        ]
    }
    
    if data:
        processed_data["original_data"] = data
        processed_data["school_name"] = data.get("school_name", "Unknown")
        processed_data["derived_teacher_name"] = data.get("derived_teacher_name", "Unknown")
    
    # 模拟一些处理时间
    import time
    time.sleep(0.1)
    
    logger.info(f"Successfully processed new teacher: {teacher_id}")
    
    return {
        "status": "success",
        "operation": "process_new_teacher",
        "result": processed_data,
        "timestamp": datetime.now().isoformat()
    }


def _update_teacher_data(teacher_id: str, data: Optional[Dict]) -> Dict[str, Any]:
    """更新教师数据"""
    logger.info(f"Updating teacher data: {teacher_id}")
    
    # 模拟数据更新逻辑
    update_summary = {
        "teacher_id": teacher_id,
        "updated_at": datetime.now().isoformat(),
        "fields_updated": []
    }
    
    if data:
        # 检查哪些字段被更新
        if "school_name" in data:
            update_summary["fields_updated"].append("school_name")
        if "derived_teacher_name" in data:
            update_summary["fields_updated"].append("derived_teacher_name")
        if "is_valid" in data:
            update_summary["fields_updated"].append("is_valid")
        
        update_summary["new_data"] = data
    
    # 模拟处理时间
    import time
    time.sleep(0.05)
    
    logger.info(f"Successfully updated teacher: {teacher_id}")
    
    return {
        "status": "success",
        "operation": "update_teacher_data",
        "result": update_summary,
        "timestamp": datetime.now().isoformat()
    }


def _sync_data(sync_type: str) -> Dict[str, Any]:
    """同步数据"""
    logger.info(f"Starting data sync: {sync_type}")
    
    # 模拟同步逻辑
    sync_stats = {
        "sync_type": sync_type,
        "started_at": datetime.now().isoformat(),
        "records_processed": 0,
        "records_updated": 0,
        "records_created": 0,
        "errors": []
    }
    
    # 根据同步类型执行不同的逻辑
    if sync_type == "daily":
        sync_stats["records_processed"] = 1500
        sync_stats["records_updated"] = 120
        sync_stats["records_created"] = 25
    elif sync_type == "hourly":
        sync_stats["records_processed"] = 200
        sync_stats["records_updated"] = 15
        sync_stats["records_created"] = 3
    else:  # manual
        sync_stats["records_processed"] = 50
        sync_stats["records_updated"] = 5
        sync_stats["records_created"] = 1
    
    # 模拟处理时间
    import time
    time.sleep(0.2)
    
    sync_stats["completed_at"] = datetime.now().isoformat()
    
    logger.info(f"Data sync completed: {sync_type}")
    
    return {
        "status": "success",
        "operation": "sync_data",
        "result": sync_stats,
        "timestamp": datetime.now().isoformat()
    }


def _handle_change_event(change_event: Optional[Dict]) -> Dict[str, Any]:
    """处理数据库变更事件"""
    if not change_event:
        raise ValueError("Change event is required")
    
    logger.info(f"Handling change event: {change_event.get('table_name')} - {change_event.get('operation')}")
    
    # 根据变更类型处理
    table_name = change_event.get("table_name")
    operation = change_event.get("operation")
    record_id = change_event.get("record_id")
    
    result = {
        "table_name": table_name,
        "operation": operation,
        "record_id": record_id,
        "processed_at": datetime.now().isoformat(),
        "actions_taken": []
    }
    
    if table_name == "derived_intl_teacher_data":
        if operation == "INSERT":
            result["actions_taken"].append("initiated_teacher_profile_creation")
            result["actions_taken"].append("scheduled_data_validation")
        elif operation == "UPDATE":
            result["actions_taken"].append("updated_search_index")
            result["actions_taken"].append("triggered_cache_refresh")
    
    elif table_name == "data_intl_wide_view":
        result["actions_taken"].append("updated_analytics_data")
        result["actions_taken"].append("triggered_report_regeneration")
    
    # 模拟处理时间
    import time
    time.sleep(0.1)
    
    logger.info(f"Change event processed successfully")
    
    return {
        "status": "success",
        "operation": "handle_change_event",
        "result": result,
        "timestamp": datetime.now().isoformat()
    } 