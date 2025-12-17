#!/usr/bin/env python3
"""
解析 Excel Web Access (EWA) XML 格式的数据
输入格式: JSON 文件
{
    "type": "xlsx",
    "data": ["xml1", "xml2", ...]
}
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from lxml import html as lxml_html


def parse_excel_xml(xml_content: str) -> Optional[pd.DataFrame]:
    """
    解析 Excel Web Access XML 数据
    
    Args:
        xml_content: XML 字符串内容
        
    Returns:
        pandas DataFrame 包含提取的表格数据
    """
    try:
        # 1. 解析 XML
        root = ET.fromstring(xml_content)
        
        # 2. 提取 CDATA 中的 JSON
        # 查找 Json 元素
        json_element = root.find('.//{*}Json')
        if json_element is None:
            json_element = root.find('.//Json')
        
        if json_element is None or json_element.text is None:
            print("错误: 未找到 JSON 元素")
            return None
        
        json_text = json_element.text.strip()
        
        # 3. 解析 JSON
        data = json.loads(json_text)
        
        # 4. 提取表格内容
        result = data.get('Result', {})
        content = result.get('Content', {})
        
        if not content:
            print("错误: 未找到 Content 数据")
            return None
        
        # 提取列信息
        column_numbers = content.get('ColumnNumbers', [])
        column_widths = content.get('ColumnWidths', [])
        
        # 提取行信息
        row_numbers = content.get('RowNumbers', [])
        row_heights = content.get('RowHeights', [])
        
        # 提取 HTML 内容
        grid_html = content.get('GridHtml', '')
        column_header_html = content.get('ColumnHeaderHtml', '')
        
        print(f"找到 {len(column_numbers)} 列, {len(row_numbers)} 行")
        
        # 5. 解析列头
        column_names = parse_column_headers(column_header_html)
        
        # 6. 解析表格数据
        rows_data = parse_grid_html(grid_html, len(row_numbers), len(column_numbers))
        
        if not rows_data:
            print("警告: 未提取到任何数据")
            return None
        
        # 7. 创建 DataFrame
        df = pd.DataFrame(rows_data)
        
        # 如果列名数量匹配,使用提取的列名
        if len(column_names) == len(df.columns):
            df.columns = column_names
        
        print(f"✓ 成功创建 DataFrame: {len(df)} 行 × {len(df.columns)} 列")
        return df
        
    except ET.ParseError as e:
        print(f"XML 解析错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return None
    except Exception as e:
        print(f"解析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_column_headers(html: str) -> List[str]:
    """解析列头 HTML - 使用 XPath"""
    try:
        tree = lxml_html.fromstring(html)
        # 提取所有列头文本 (class="ewr-chc" 或 "ewr-cchc")
        headers = tree.xpath('//div[contains(@class, "ewr-chc") or contains(@class, "ewr-cchc")]/text()')
        return [h.strip() for h in headers if h.strip()]
    except Exception as e:
        print(f"列头解析出错: {e}")
        return []


def parse_grid_html_xpath(html_str: str) -> List[List[str]]:
    """
    使用 XPath 从 GridHtml 中提取表格数据
    
    Args:
        html_str: HTML 字符串
        
    Returns:
        二维列表包含单元格数据
    """
    try:
        # 解析 HTML
        tree = lxml_html.fromstring(html_str)
        
        # 找到 gridRows 容器
        grid_rows = tree.xpath('//div[@id="gridRows"]')
        if not grid_rows:
            return []
        
        # 提取所有行 (class="ewr-nglr")
        row_elements = grid_rows[0].xpath('.//div[contains(@class, "ewr-nglr")]')
        
        rows_data = []
        for row_elem in row_elements:
            # 提取该行的所有单元格 (class="ewr-ca")
            cell_elements = row_elem.xpath('.//div[contains(@class, "ewr-ca")]')
            
            row_cells = []
            for cell_elem in cell_elements:
                # 提取单元格的文本内容（递归获取所有文本）
                cell_text = ''.join(cell_elem.xpath('.//text()')).strip()
                row_cells.append(cell_text)
            
            if row_cells:  # 只添加非空行
                rows_data.append(row_cells)
        
        return rows_data
        
    except Exception as e:
        print(f"XPath 解析出错: {e}")
        return []


def parse_grid_html(html: str, num_rows: int, num_cols: int) -> List[List[str]]:
    """
    解析表格 HTML 内容 - 使用 XPath 从 gridRows 结构中提取
    
    Args:
        html: HTML 字符串
        num_rows: 预期行数
        num_cols: 预期列数
        
    Returns:
        二维列表包含单元格数据
    """
    rows = parse_grid_html_xpath(html)
    
    if not rows:
        print("警告: 未能从 HTML 中提取到数据")
        return []
    
    print(f"提取到 {len(rows)} 行数据")
    if rows:
        print(f"第一行有 {len(rows[0])} 个单元格")
    
    # 确保每行的列数一致
    max_cols = max(len(row) for row in rows) if rows else num_cols
    for row in rows:
        while len(row) < max_cols:
            row.append('')
    
    return rows




def parse_excel_json(json_content: str) -> Optional[pd.DataFrame]:
    """
    解析包含多个 XML 的 JSON 数据
    
    JSON 格式:
    {
        "type": "xlsx",
        "data": ["xml1", "xml2", ...]
    }
    
    Args:
        json_content: JSON 字符串内容
        
    Returns:
        合并后的 pandas DataFrame
    """
    try:
        # 解析 JSON
        json_data = json.loads(json_content)
        
        if not isinstance(json_data, dict):
            print("错误: JSON 内容不是对象格式")
            return None
        
        data_list = json_data.get('data', [])
        
        if not data_list:
            print("错误: data 数组为空")
            return None
        
        print(f"包含 {len(data_list)} 个 XML 数据块")
        
        # 解析每个 XML 并收集 DataFrame
        all_dfs = []
        for i, xml_content in enumerate(data_list, 1):
            print(f"正在解析第 {i}/{len(data_list)} 个数据块...")
            
            df = parse_excel_xml(xml_content)
            if df is not None and not df.empty:
                all_dfs.append(df)
            else:
                print(f"警告: 第 {i} 个 XML 数据块解析失败或为空")
        
        if not all_dfs:
            print("错误: 没有成功解析任何数据")
            return None
        
        # 合并所有 DataFrame
        print(f"正在合并 {len(all_dfs)} 个数据块...")
        merged_df = pd.concat(all_dfs, ignore_index=True)
        print(f"✓ 合并完成: 总共 {len(merged_df)} 行 × {len(merged_df.columns)} 列")
        
        return merged_df
        
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return None
    except Exception as e:
        print(f"处理过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数 - 示例用法"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='解析 Excel Web Access JSON 格式的数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本用法
  python parse_excel_xml.py data.json
  
  # 指定输出文件
  python parse_excel_xml.py data.json output.xlsx
  
  # 导出为 CSV
  python parse_excel_xml.py data.json output.csv
  
JSON 文件格式:
  {
      "type": "xlsx",
      "data": ["<xml>...</xml>", "<xml>...</xml>", ...]
  }
        '''
    )
    
    parser.add_argument('json_file', help='输入的 JSON 文件路径')
    parser.add_argument('output_file', nargs='?', help='输出的 Excel/CSV 文件路径 (可选)')
    
    args = parser.parse_args()
    
    json_file = Path(args.json_file)
    
    if not json_file.exists():
        print(f"错误: 文件不存在: {json_file}")
        return
    
    # 读取 JSON 文件
    print(f"正在读取文件: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 JSON 数据
    df = parse_excel_json(content)
    
    if df is None or df.empty:
        print("解析失败或没有数据")
        return
    
    print("\n数据预览:")
    print(df.head(10))
    print(f"\n数据形状: {df.shape}")
    
    # 保存结果
    if args.output_file:
        output_file = Path(args.output_file)
    else:
        output_file = json_file.with_suffix('.xlsx')
    
    print(f"\n正在保存到: {output_file}")
    
    # 根据文件扩展名选择保存格式
    if output_file.suffix.lower() == '.csv':
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
    else:
        df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"✓ 成功保存 {len(df)} 行数据到 {output_file}")


if __name__ == '__main__':
    main()

