"""
Elasticsearch索引管理插件
处理教师数据的索引和搜索
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List


# 配置日志
logger = logging.getLogger(__name__)


def index_data(operation: str = "update_teacher_index",
               teacher_id: Optional[str] = None,
               data: Optional[Dict] = None,
               index_name: str = "teachers",
               batch_size: int = 100,
               change_event: Optional[Dict] = None,
               **kwargs) -> Dict[str, Any]:
    """
    ES索引主函数
    
    Args:
        operation: 操作类型
        teacher_id: 教师ID
        data: 数据对象
        index_name: 索引名称
        batch_size: 批处理大小
        change_event: 数据库变更事件
        **kwargs: 其他参数
    
    Returns:
        索引结果字典
    """
    logger.info(f"env {os.getenv('ES_PASSWORD')}")
    logger.info(f"env {os.getenv('HELLO')}")
    logger.info(f"==！！！！！！！！===uer_index")
    logger.info(f"Starting ES indexing: operation={operation}, index={index_name}")
    
    try:
        if operation == "update_teacher_index":
            return _update_teacher_index(teacher_id, data, index_name)
        elif operation == "bulk_index":
            return _bulk_index(data, index_name, batch_size)
        elif operation == "delete_index":
            return _delete_from_index(teacher_id, index_name)
        elif operation == "handle_change_event":
            return _handle_index_change_event(change_event, index_name)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"ES indexing failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def _update_teacher_index(teacher_id: str, data: Optional[Dict], index_name: str) -> Dict[str, Any]:
    """更新教师索引"""
    logger.info(f"Updating teacher index: {teacher_id}")
    
    # 模拟ES索引操作
    document = {
        "teacher_id": teacher_id,
        "indexed_at": datetime.now().isoformat(),
        "index_name": index_name
    }
    
    if data:
        # 处理索引数据
        document.update({
            "school_name": data.get("school_name", ""),
            "derived_teacher_name": data.get("derived_teacher_name", ""),
            "is_valid": data.get("is_valid", False),
            "description": data.get("description", ""),
            # 添加搜索友好的字段
            "name_suggest": _create_suggest_field(data.get("derived_teacher_name", "")),
            "school_suggest": _create_suggest_field(data.get("school_name", ""))
        })
    
    # 模拟ES操作时间
    import time
    time.sleep(0.05)
    
    logger.info(f"Successfully indexed teacher: {teacher_id}")
    
    return {
        "status": "success",
        "operation": "update_teacher_index",
        "result": {
            "teacher_id": teacher_id,
            "index_name": index_name,
            "document_size": len(json.dumps(document)),
            "fields_indexed": list(document.keys())
        },
        "timestamp": datetime.now().isoformat()
    }


def _bulk_index(data: Optional[Dict], index_name: str, batch_size: int) -> Dict[str, Any]:
    """批量索引"""
    logger.info(f"Starting bulk indexing: batch_size={batch_size}")
    
    # 模拟批量索引数据
    if not data or "records" not in data:
        # 生成模拟数据
        records = [
            {
                "teacher_id": f"teacher_{i}",
                "school_name": f"School_{i % 10}",
                "derived_teacher_name": f"Teacher {i}",
                "is_valid": i % 3 == 0
            }
            for i in range(batch_size)
        ]
    else:
        records = data["records"]
    
    # 模拟批量处理
    batches = [records[i:i + batch_size] for i in range(0, len(records), batch_size)]
    
    indexed_count = 0
    failed_count = 0
    
    for batch_idx, batch in enumerate(batches):
        logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")
        
        # 模拟批量索引操作
        for record in batch:
            try:
                # 简单的验证
                if record.get("teacher_id"):
                    indexed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to index record: {e}")
                failed_count += 1
        
        # 模拟处理时间
        import time
        time.sleep(0.02)
    
    logger.info(f"Bulk indexing completed: {indexed_count} indexed, {failed_count} failed")
    
    return {
        "status": "success",
        "operation": "bulk_index",
        "result": {
            "total_records": len(records),
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "batch_count": len(batches),
            "index_name": index_name
        },
        "timestamp": datetime.now().isoformat()
    }


def _delete_from_index(teacher_id: str, index_name: str) -> Dict[str, Any]:
    """从索引中删除"""
    logger.info(f"Deleting from index: {teacher_id}")
    
    # 模拟删除操作
    import time
    time.sleep(0.02)
    
    logger.info(f"Successfully deleted teacher from index: {teacher_id}")
    
    return {
        "status": "success",
        "operation": "delete_index",
        "result": {
            "teacher_id": teacher_id,
            "index_name": index_name,
            "deleted_at": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }


def _handle_index_change_event(change_event: Optional[Dict], index_name: str) -> Dict[str, Any]:
    """处理索引变更事件"""
    if not change_event:
        raise ValueError("Change event is required")
    
    logger.info(f"Handling index change event: {change_event.get('operation')}")
    
    operation = change_event.get("operation")
    record_id = change_event.get("record_id")
    new_data = change_event.get("new_data")
    
    result = {
        "operation": operation,
        "record_id": record_id,
        "index_name": index_name,
        "processed_at": datetime.now().isoformat(),
        "actions_taken": []
    }
    
    if operation == "INSERT":
        # 新增索引
        if new_data:
            _update_teacher_index(record_id, new_data, index_name)
            result["actions_taken"].append("created_new_index_document")
    
    elif operation == "UPDATE":
        # 更新索引
        if new_data:
            _update_teacher_index(record_id, new_data, index_name)
            result["actions_taken"].append("updated_index_document")
    
    elif operation == "DELETE":
        # 删除索引
        _delete_from_index(record_id, index_name)
        result["actions_taken"].append("deleted_index_document")
    
    # 模拟处理时间
    import time
    time.sleep(0.05)
    
    logger.info(f"Index change event processed successfully")
    
    return {
        "status": "success",
        "operation": "handle_index_change_event",
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


def _create_suggest_field(text: str) -> List[str]:
    """创建搜索建议字段"""
    if not text:
        return []
    
    # 简单的分词和建议生成
    words = text.split()
    suggestions = []
    
    # 完整文本
    suggestions.append(text.lower())
    
    # 单词
    for word in words:
        if len(word) > 2:
            suggestions.append(word.lower())
    
    # 前缀
    for i in range(2, min(len(text), 10)):
        suggestions.append(text[:i].lower())
    
    return list(set(suggestions))  # 去重 