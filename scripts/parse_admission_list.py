#!/usr/bin/env python3
"""
解析录取名单数据的脚本。
支持解析XML格式的录取名单数据，并输出为结构化格式。
支持处理不同列数的数据格式。
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
from xml.etree import ElementTree as ET

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 表头关键词
HEADER_KEYWORDS = {'姓名', '报考', '录取', '编号'}

@dataclass
class TextElement:
    """基础文本元素"""
    text: str
    is_bold: bool
    font_size: float
    
    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Optional['TextElement']:
        """从XML元素创建文本元素"""
        try:
            # 获取文本内容
            text = element.text if element.text else ""
            if not text.strip():
                return None
                
            # 解析属性
            is_bold = element.get('b') == '1'
            # 从高度属性估算字体大小
            font_size = float(element.get('h', 0))
            
            return cls(
                text=text.strip(),
                is_bold=is_bold,
                font_size=font_size
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing element attributes: {e}")
            return None
    
    def is_title(self) -> bool:
        """判断是否为标题行"""
        # 标题通常是加粗的，字体较大，且字段数较少
        words = self.text.split()
        return (self.is_bold or self.font_size > 15) and len(words) < 5
    
    def is_header(self) -> bool:
        """判断是否为表头行"""
        # 包含关键词，但不是标题
        has_keywords = any(keyword in self.text for keyword in HEADER_KEYWORDS)
        words = self.text.split()
        return has_keywords and len(words) >= 3 and not self.is_title()

@dataclass
class AdmissionRecord:
    """录取记录数据模型"""
    raw_text: str  # 原始文本
    fields: Dict[str, str]  # 解析后的字段
    
    @classmethod
    def from_xml_element(cls, element: ET.Element) -> Optional['AdmissionRecord']:
        """从XML元素创建录取记录"""
        text_elem = TextElement.from_xml_element(element)
        if not text_elem:
            return None
            
        # 如果是标题或表头，返回None
        if text_elem.is_title() or text_elem.is_header():
            return None
            
        # 分割字段
        fields = text_elem.text.split()
        
        # 如果字段太少，可能不是数据行
        if len(fields) < 3:
            return None
            
        return cls(
            raw_text=text_elem.text,
            fields={'field_' + str(i): field for i, field in enumerate(fields, 1)}
        )

class AdmissionListParser:
    """录取名单解析器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        
    def parse_admission_json(self, json_file: str) -> Dict[str, Any]:
        """解析录取名单JSON文件"""
        json_path = self.data_dir / json_file
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or 'data' not in data:
                logger.error(f"Invalid JSON format in {json_file}")
                return {'headers': [], 'records': [], 'max_fields': 0}
                
            all_records = []
            max_fields = 0
            headers = None
            title = None
            
            for xml_str in data['data']:
                page_title, page_headers, page_records = self._parse_xml_string(xml_str)
                
                # 更新最大字段数
                for record in page_records:
                    max_fields = max(max_fields, len(record.fields))
                
                # 使用第一个找到的标题和表头
                if not title and page_title:
                    title = page_title
                if not headers and page_headers:
                    headers = page_headers
                
                all_records.extend(page_records)
            
            # 如果没有找到表头，生成默认表头
            if not headers:
                headers = [f'字段{i}' for i in range(1, max_fields + 1)]
            
            # 确保所有记录都有相同数量的字段
            for record in all_records:
                for i in range(1, max_fields + 1):
                    field_key = f'field_{i}'
                    if field_key not in record.fields:
                        record.fields[field_key] = ""
                
            return {
                'title': title,
                'headers': headers,
                'records': all_records,
                'max_fields': max_fields
            }
            
        except Exception as e:
            logger.error(f"Error parsing {json_file}: {str(e)}")
            return {'title': None, 'headers': [], 'records': [], 'max_fields': 0}
            
    def _parse_xml_string(self, xml_str: str) -> Tuple[Optional[str], List[str], List[AdmissionRecord]]:
        """
        解析XML字符串中的录取记录
        
        Returns:
            tuple: (标题, 表头字段列表, 记录列表)
        """
        try:
            root = ET.fromstring(xml_str)
            title = None
            headers = []
            records = []
            
            # 解析所有文本元素
            for text_elem in root.findall(".//T"):
                element = TextElement.from_xml_element(text_elem)
                if not element:
                    continue
                    
                # 识别标题
                if not title and element.is_title():
                    title = element.text
                    continue
                    
                # 识别表头
                if not headers and element.is_header():
                    headers = element.text.split()
                    continue
                    
                # 解析数据行
                record = AdmissionRecord.from_xml_element(text_elem)
                if record:
                    records.append(record)
                    
            return title, headers, records
            
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {str(e)}")
            return None, [], []
            
    def save_to_json(self, data: Dict[str, Any], output_file: str):
        """保存记录为JSON格式"""
        output_path = Path(output_file)
        
        try:
            # 转换记录为字典格式
            output_data = {
                'title': data['title'],
                'headers': data['headers'],
                'max_fields': data['max_fields'],
                'records': [
                    {
                        'raw_text': record.raw_text,
                        'fields': record.fields
                    }
                    for record in data['records']
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data['records'])} records to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to {output_file}: {str(e)}")
            
    def save_to_csv(self, data: Dict[str, Any], output_file: str):
        """保存记录为CSV格式"""
        import csv
        output_path = Path(output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # 写入标题（如果有）
                if data['title']:
                    writer.writerow(['标题:', data['title']])
                    writer.writerow([])  # 空行
                
                # 写入表头
                writer.writerow(data['headers'])
                
                # 写入数据
                for record in data['records']:
                    # 按顺序获取字段值
                    row = [record.fields.get(f'field_{i}', "") 
                          for i in range(1, data['max_fields'] + 1)]
                    writer.writerow(row)
                    
            logger.info(f"Saved {len(data['records'])} records to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving to {output_file}: {str(e)}")

def main():
    # 设置数据目录
    data_dir = Path(__file__).parent.parent / 'data' / '录取名单'
    parser = AdmissionListParser(data_dir)
    
    # 解析录取名单
    data = parser.parse_admission_json('第一批拟录取名单.json')
    
    if data['records']:
        # 保存为JSON格式
        parser.save_to_json(data, data_dir / '第一批拟录取名单_records.json')
        # 保存为CSV格式
        parser.save_to_csv(data, data_dir / '第一批拟录取名单_records.csv')
    else:
        logger.warning("No records found to save")

if __name__ == '__main__':
    main()