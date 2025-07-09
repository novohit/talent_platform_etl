"""
教师数据消费者
"""

from typing import Dict, Any
from ..base_consumer import BaseConsumer
from ..canal_client import ChangeEvent
from talent_platform.logger import logger


class TeacherConsumer(BaseConsumer):
    """教师数据消费者 - 处理教师相关表的数据变更"""
    
    def __init__(self):
        super().__init__("teacher_consumer")
        
        # 配置要监听的教师相关表
        self.add_filter("talent_platform", "derived_intl_teacher_data", {"INSERT", "UPDATE", "DELETE"})
        self.add_filter("talent_platform", "data_intl_wide_view", {"INSERT", "UPDATE"})
        self.add_filter("talent_platform", "teacher_profiles", {"UPDATE"})
    
    def process_event(self, event: ChangeEvent):
        """处理教师数据变更事件"""
        logger.info(f"TeacherConsumer received event: {event.database}.{event.table} - {event.event_type}")
        
        # 根据不同的表调用不同的处理逻辑
        if event.table == "derived_intl_teacher_data":
            self._handle_teacher_data_change(event)
        elif event.table == "data_intl_wide_view":
            self._handle_teacher_wide_view_change(event)
        elif event.table == "teacher_profiles":
            self._handle_teacher_profile_change(event)
        else:
            logger.debug(f"No specific handler for table: {event.table}")
    
    def _handle_teacher_data_change(self, event: ChangeEvent):
        """处理教师基础数据变更"""
        if event.event_type == "INSERT":
            # 新教师数据插入，触发数据处理插件
            teacher_data = event.data
            teacher_id = teacher_data.get("id") or teacher_data.get("teacher_id")
            
            if teacher_id:
                parameters = {
                    "operation": "process_new_teacher",
                    "teacher_id": teacher_id,
                    "data": teacher_data,
                    "source_table": "derived_intl_teacher_data"
                }
                
                self.trigger_plugin("data_processor", parameters, priority="normal")
                
                # 同时触发ES索引更新
                self.trigger_plugin("es_indexer", {
                    "operation": "index_teacher",
                    "teacher_id": teacher_id,
                    "data": teacher_data
                }, priority="normal")
        
        elif event.event_type == "UPDATE":
            # 教师数据更新，触发ES索引更新
            before_data = event.data.get("before", {})
            after_data = event.data.get("after", {})
            teacher_id = after_data.get("id") or after_data.get("teacher_id")
            
            if teacher_id:
                # 检查关键字段是否有变更
                key_fields = ["email", "status", "certification_status", "subject_areas"]
                has_key_changes = any(
                    before_data.get(field) != after_data.get(field) 
                    for field in key_fields
                )
                
                if has_key_changes:
                    # 高优先级处理关键字段变更
                    parameters = {
                        "operation": "update_teacher_index",
                        "teacher_id": teacher_id,
                        "before": before_data,
                        "after": after_data,
                        "priority_update": True
                    }
                    
                    self.trigger_plugin("es_indexer", parameters, priority="high")
                else:
                    # 普通字段更新
                    parameters = {
                        "operation": "update_teacher_index",
                        "teacher_id": teacher_id,
                        "data": after_data
                    }
                    
                    self.trigger_plugin("es_indexer", parameters, priority="normal")
        
        elif event.event_type == "DELETE":
            # 教师数据删除，从ES中移除索引
            teacher_data = event.data
            teacher_id = teacher_data.get("id") or teacher_data.get("teacher_id")
            
            if teacher_id:
                parameters = {
                    "operation": "delete_teacher_index",
                    "teacher_id": teacher_id
                }
                
                self.trigger_plugin("es_indexer", parameters, priority="high")
    
    def _handle_teacher_wide_view_change(self, event: ChangeEvent):
        """处理教师宽表数据变更"""
        if event.event_type in ["INSERT", "UPDATE"]:
            teacher_data = event.data if event.event_type == "INSERT" else event.data.get("after", {})
            teacher_id = teacher_data.get("teacher_id") or teacher_data.get("id")
            
            if teacher_id:
                # 宽表数据变更，触发教师分析插件
                parameters = {
                    "operation": "analyze_teacher_profile",
                    "teacher_id": teacher_id,
                    "wide_view_data": teacher_data,
                    "event_type": event.event_type
                }
                
                # 宽表数据通常包含分析相关信息，使用中等优先级
                self.trigger_plugin("data_processor", parameters, priority="normal")
    
    def _handle_teacher_profile_change(self, event: ChangeEvent):
        """处理教师档案更新"""
        if event.event_type == "UPDATE":
            before_data = event.data.get("before", {})
            after_data = event.data.get("after", {})
            teacher_id = after_data.get("teacher_id") or after_data.get("id")
            
            if teacher_id:
                # 检查是否是重要档案信息更新
                important_fields = ["resume", "education", "experience", "skills", "bio"]
                updated_fields = []
                
                for field in important_fields:
                    if before_data.get(field) != after_data.get(field):
                        updated_fields.append(field)
                
                if updated_fields:
                    # 档案重要信息更新，触发多个插件
                    parameters = {
                        "operation": "update_teacher_profile",
                        "teacher_id": teacher_id,
                        "updated_fields": updated_fields,
                        "before": before_data,
                        "after": after_data
                    }
                    
                    # 更新ES索引
                    self.trigger_plugin("es_indexer", parameters, priority="normal")
                    
                    # 重新分析教师能力
                    analysis_params = {
                        "operation": "reanalyze_teacher_skills",
                        "teacher_id": teacher_id,
                        "profile_data": after_data
                    }
                    self.trigger_plugin("data_processor", analysis_params, priority="low")
    
    def on_error(self, event: ChangeEvent, error: Exception):
        """教师数据处理错误处理"""
        logger.error(f"TeacherConsumer error processing {event.database}.{event.table}: {error}")
        
        # 对于教师数据错误，记录到错误处理系统
        try:
            parameters = {
                "operation": "log_teacher_data_error",
                "error_type": "teacher_consumer_error",
                "table": event.table,
                "event": event.to_dict(),
                "error_message": str(error),
                "timestamp": event.timestamp.isoformat()
            }
            
            self.trigger_plugin("error_handler", parameters, priority="high")
        except Exception as e:
            logger.error(f"Failed to trigger error handler for teacher data: {e}") 