"""
Canal客户端封装
"""

import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from talent_platform.logger import logger
from canal.client import Client
from canal.protocol import EntryProtocol_pb2
from canal.protocol import CanalProtocol_pb2


@dataclass
class ChangeEvent:
    """数据库变更事件"""
    database: str
    table: str
    event_type: str  # INSERT, UPDATE, DELETE
    data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'database': self.database,
            'table': self.table,
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }


class CanalClient:
    """Canal客户端封装"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 11111, 
                 destination: str = 'example', username: str = '', password: str = ''):
        self.host = host
        self.port = port
        self.destination = destination
        self.username = username
        self.password = password
        
        self.client = None
        self.connected = False
        self.running = False
        
        # 事件处理器列表
        self.event_handlers: List[Callable[[ChangeEvent], None]] = []
    
    def connect(self) -> bool:
        """连接到Canal服务器"""
        try:
            self.client = Client()
            self.client.connect(host=self.host, port=self.port)
            
            # 检查连接有效性
            self.client.check_valid(username=self.username, password=self.password)
            
            # 订阅
            self.client.subscribe(client_id=b'canal_consumer', destination=self.destination)
            
            self.connected = True
            logger.info(f"Connected to Canal server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Canal server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client and self.connected:
            try:
                self.client.disconnect()
                logger.info("Disconnected from Canal server")
            except Exception as e:
                logger.error(f"Error disconnecting from Canal: {e}")
            finally:
                self.connected = False
                self.running = False
    
    def add_event_handler(self, handler: Callable[[ChangeEvent], None]):
        """添加事件处理器"""
        self.event_handlers.append(handler)
        logger.info(f"Added event handler: {handler.__name__}")
    
    def remove_event_handler(self, handler: Callable[[ChangeEvent], None]):
        """移除事件处理器"""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
            logger.info(f"Removed event handler: {handler.__name__}")
    
    def _parse_message(self, message) -> List[ChangeEvent]:
        """解析Canal消息为变更事件"""
        events = []
        
        try:
            entries = message.get('entries', [])
            
            for entry in entries:
                entry_type = entry.entryType
                
                # 跳过事务开始/结束事件
                if entry_type in [EntryProtocol_pb2.EntryType.TRANSACTIONBEGIN, 
                                 EntryProtocol_pb2.EntryType.TRANSACTIONEND]:
                    continue
                
                # 解析行变更数据
                row_change = EntryProtocol_pb2.RowChange()
                row_change.MergeFromString(entry.storeValue)
                
                header = entry.header
                database = header.schemaName
                table = header.tableName
                event_type_code = row_change.eventType
                
                # 转换事件类型
                event_type_map = {
                    EntryProtocol_pb2.EventType.INSERT: 'INSERT',
                    EntryProtocol_pb2.EventType.UPDATE: 'UPDATE',
                    EntryProtocol_pb2.EventType.DELETE: 'DELETE'
                }
                
                event_type = event_type_map.get(event_type_code, 'UNKNOWN')
                if event_type == 'UNKNOWN':
                    continue
                
                # 解析每一行数据
                for row in row_change.rowDatas:
                    format_data = {}
                    
                    if event_type == 'DELETE':
                        # 删除事件只有before数据
                        for column in row.beforeColumns:
                            format_data[column.name] = column.value
                    elif event_type == 'INSERT':
                        # 插入事件只有after数据
                        for column in row.afterColumns:
                            format_data[column.name] = column.value
                    else:  # UPDATE
                        # 更新事件包含before和after数据
                        format_data['before'] = {}
                        format_data['after'] = {}
                        
                        for column in row.beforeColumns:
                            format_data['before'][column.name] = column.value
                        for column in row.afterColumns:
                            format_data['after'][column.name] = column.value
                    
                    # 创建变更事件
                    event = ChangeEvent(
                        database=database,
                        table=table,
                        event_type=event_type,
                        data=format_data,
                        timestamp=datetime.now()
                    )
                    
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"Error parsing Canal message: {e}")
        
        return events
    
    def _handle_events(self, events: List[ChangeEvent]):
        """处理变更事件"""
        for event in events:
            logger.debug(f"Processing event: {event.database}.{event.table} - {event.event_type}")
            
            # 调用所有事件处理器
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}")
    
    def start_consuming(self, batch_size: int = 100, timeout: int = 1):
        """开始消费消息"""
        if not self.connected:
            if not self.connect():
                return False
        
        self.running = True
        logger.info("Started consuming Canal messages...")
        
        try:
            while self.running:
                try:
                    # 获取消息
                    message = self.client.get(batch_size)
                    
                    if message:
                        # 解析消息
                        events = self._parse_message(message)
                        
                        if events:
                            logger.debug(f"Received {len(events)} change events")
                            self._handle_events(events)
                    
                    # 短暂休眠
                    time.sleep(timeout)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping...")
                    break
                except Exception as e:
                    logger.error(f"Error consuming messages: {e}")
                    time.sleep(5)  # 错误时等待更长时间
                    
        finally:
            self.running = False
            self.disconnect()
        
        logger.info("Stopped consuming Canal messages")
        return True
    
    def stop_consuming(self):
        """停止消费消息"""
        self.running = False
        logger.info("Stopping Canal message consumption...")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and self.connected 