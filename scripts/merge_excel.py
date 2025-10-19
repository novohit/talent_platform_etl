#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
from pathlib import Path
import logging
from typing import List, Tuple
import numpy as np

def remove_duplicates_by_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    移除重复的teacher_name，保留index列值最小的记录
    
    Args:
        df (pd.DataFrame): 包含teacher_name和index列的数据框
        
    Returns:
        pd.DataFrame: 去除重复名字后的数据框
    """
    required_columns = ['teacher_name', 'index']
    for col in required_columns:
        if col not in df.columns:
            logger.warning(f"数据中没有{col}列，跳过去重处理")
            return df
        
    # 记录去重前的行数
    original_count = len(df)
    
    # 确保index列是数值类型
    df['index'] = pd.to_numeric(df['index'], errors='coerce')
    
    # 按teacher_name分组，对每组按index排序，保留最小index的记录
    df = df.sort_values('index').drop_duplicates(subset=['teacher_name'], keep='first')
    
    # 记录去重后的行数
    deduped_count = len(df)
    removed_count = original_count - deduped_count
    
    if removed_count > 0:
        logger.info(f"去重完成: 删除了 {removed_count} 条重复记录 (原始: {original_count}, 去重后: {deduped_count})")
        # 显示被删除的重复记录数量
        duplicates = df.groupby('teacher_name').size()
        duplicate_counts = duplicates[duplicates > 1]
        if not duplicate_counts.empty:
            logger.info("重复记录统计:")
            for name, count in duplicate_counts.items():
                logger.info(f"  - {name}: {count}条记录")
    else:
        logger.info("数据中没有重复的teacher_name")
        
    return df

def exclude_by_values(df: pd.DataFrame, exclude_conditions: dict) -> pd.DataFrame:
    """
    从数据框中排除特定列中包含指定值的行
    
    Args:
        df (pd.DataFrame): 要过滤的数据框
        exclude_conditions (dict): 排除条件字典，格式为：
            {
                'column_name': {
                    'values': List[str],  # 要排除的值列表
                    'match_type': str     # 匹配类型：'any'（任意匹配则排除）或'all'（全部匹配才排除）
                }
            }
            
    Returns:
        pd.DataFrame: 排除指定值后的数据框
    """
    if not exclude_conditions:
        return df
        
    original_count = len(df)
    result_df = df.copy()
    
    for column, condition in exclude_conditions.items():
        if column not in df.columns:
            logger.warning(f"列 {column} 不存在，跳过此排除条件")
            continue
            
        values = condition.get('values', [])
        match_type = condition.get('match_type', 'any')
        
        if not values:
            continue
            
        # 创建排除掩码
        if match_type == 'all':
            # 必须匹配所有值才排除
            exclude_mask = pd.Series([True] * len(df))
            for value in values:
                exclude_mask &= df[column].astype(str).str.contains(str(value), na=False)
        else:
            # 匹配任意值就排除
            pattern = '|'.join(map(str, values))
            exclude_mask = df[column].astype(str).str.contains(pattern, na=False)
        
        # 保留不匹配的行
        result_df = result_df[~exclude_mask]
        
        excluded_count = len(df) - len(result_df)
        if excluded_count > 0:
            logger.info(f"从列 {column} 中排除了 {excluded_count} 行包含 {values} 的数据")
    
    final_count = len(result_df)
    total_excluded = original_count - final_count
    if total_excluded > 0:
        logger.info(f"总计排除了 {total_excluded} 行数据 (原始: {original_count}, 剩余: {final_count})")
    
    return result_df

def filter_dataframe(df: pd.DataFrame, filter_conditions: dict) -> pd.DataFrame:
    """
    根据指定的过滤条件过滤数据框
    
    Args:
        df (pd.DataFrame): 要过滤的数据框
        filter_conditions (dict): 过滤条件字典，格式为：
            {
                'column_name': {
                    'values': List[str],  # 要匹配的值列表
                    'match_type': str     # 匹配类型：'any'（任意匹配）或'all'（全部匹配）
                }
            }
    
    Returns:
        pd.DataFrame: 过滤后的数据框
    """
    if not filter_conditions:
        return df
        
    combined_mask = pd.Series([True] * len(df))
    
    for column, condition in filter_conditions.items():
        if column not in df.columns:
            logger.warning(f"列 {column} 不存在，跳过此过滤条件")
            continue
            
        values = condition.get('values', [])
        match_type = condition.get('match_type', 'any')
        
        if not values:
            continue
            
        # 创建模式
        pattern = '|'.join(values)
        
        # 创建当前列的掩码
        current_mask = df[column].str.contains(pattern, na=False)
        
        # 根据匹配类型组合掩码
        if match_type == 'all':
            # 必须匹配所有值
            for value in values:
                current_mask &= df[column].str.contains(value, na=False)
        # 'any'情况下使用默认的pattern匹配即可
        
        combined_mask &= current_mask
    
    return df[combined_mask]

def split_first_last_name(full_name: str) -> Tuple[str, str]:
    """
    将全名分割为名字和姓氏
    
    Args:
        full_name (str): 完整姓名
        
    Returns:
        Tuple[str, str]: (名字, 姓氏)
    """
    try:
        if pd.isna(full_name) or not isinstance(full_name, str):
            return '', ''
            
        # 分割名字为部分
        name_parts = full_name.strip().split()
        
        if not name_parts:
            return '', ''
            
        # 对于大多数情况，最后一部分是姓氏，前面的是名字
        if len(name_parts) > 2:
            # 检查是否有中间名缩写（包含点号）
            if '.' in name_parts[-2]:
                first_name = ' '.join(name_parts[:-1])
                last_name = name_parts[-1]
            else:
                # 否则将最后一部分作为姓氏，其余作为名字
                first_name = ' '.join(name_parts[:-1])
                last_name = name_parts[-1]
        else:
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return first_name.strip(), last_name.strip()
    except Exception as e:
        logger.warning(f"处理姓名时出错 '{full_name}': {str(e)}")
        return '', ''

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（当前脚本所在目录的上一级）
root_dir = os.path.dirname(current_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def merge_excel_files(
    file_names: List[str], 
    output_name: str, 
    sheet_name: str | int = 0,
    filter_conditions: dict = None,
    exclude_conditions: dict = None
) -> str:
    """
    合并指定的Excel文件列表，可选择性地应用过滤和排除条件
    
    Args:
        file_names (List[str]): 要合并的Excel文件名列表（文件应位于data目录下）
        output_name (str): 输出文件名（将保存在data目录下）
        sheet_name (str | int): 要读取的sheet名称或索引，默认为第一个sheet (0)
                               可以是sheet的名称或索引号(0-based)
        filter_conditions (dict, optional): 过滤条件字典，格式为：
            {
                'column_name': {
                    'values': List[str],  # 要匹配的值列表
                    'match_type': str     # 匹配类型：'any'（任意匹配）或'all'（全部匹配）
                }
            }
            例如：
            {
                'major_paper1_domain': {
                    'values': ['自动化类', '机械类'],
                    'match_type': 'any'
                }
            }
        exclude_conditions (dict, optional): 排除条件字典，格式与filter_conditions相同，
            但是会排除匹配的行而不是保留。例如：
            {
                'status': {
                    'values': ['已删除', '无效'],
                    'match_type': 'any'  # 匹配任意一个值就排除
                }
            }
    
    Returns:
        str: 合并后的文件完整路径
    """
    try:
        # 设置data目录路径
        data_dir = Path(root_dir) / 'data'
        if not data_dir.exists():
            raise FileNotFoundError(f"data目录不存在: {data_dir}")

        # 验证所有输入文件
        excel_files = []
        for file_name in file_names:
            file_path = data_dir / file_name
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_name}")
                continue
            if not file_path.suffix in ['.xlsx', '.xls']:
                logger.warning(f"不支持的文件格式: {file_name}")
                continue
            excel_files.append(file_path)

        if not excel_files:
            raise FileNotFoundError("没有找到有效的Excel文件")

        logger.info(f"开始处理 {len(excel_files)} 个Excel文件")

        # 读取并合并所有Excel文件
        all_dfs = []
        for file in excel_files:
            try:
                logger.info(f"正在处理文件: {file.name}")
                # 首先获取所有工作表名称
                excel_file = pd.ExcelFile(file)
                sheet_names = excel_file.sheet_names
                
                # 如果指定了sheet索引，确保它是有效的
                if isinstance(sheet_name, int):
                    if sheet_name < 0 or sheet_name >= len(sheet_names):
                        logger.warning(f"文件 {file.name} 的sheet索引 {sheet_name} 无效，将使用第一个sheet")
                        sheet_name = 0
                # 如果指定了sheet名称，确保它存在
                elif isinstance(sheet_name, str) and sheet_name not in sheet_names:
                    logger.warning(f"文件 {file.name} 中没有找到sheet '{sheet_name}'，将使用第一个sheet")
                    sheet_name = 0
                
                # 读取指定的工作表
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                logger.info(f"成功读取工作表: {sheet_names[sheet_name] if isinstance(sheet_name, int) else sheet_name}")
                
                # 检查是否存在teacher_name列
                if 'teacher_name' not in df.columns:
                    logger.warning(f"文件 {file.name} 中没有找到teacher_name列，跳过处理")
                    continue
                    
                # 添加first_name和last_name列
                logger.info("正在处理姓名分割...")
                # 使用apply函数应用split_first_last_name函数到每个teacher_name
                names_split = df['teacher_name'].apply(split_first_last_name)
                
                # 获取当前列的顺序
                columns = df.columns.tolist()
                # 找到teacher_name的位置
                teacher_name_pos = columns.index('teacher_name')
                
                # 创建新的DataFrame，按照所需顺序排列列
                new_columns = (
                    columns[:teacher_name_pos + 1]  # teacher_name之前的列（包括teacher_name）
                    + ['first_name', 'last_name']   # 插入新列
                    + columns[teacher_name_pos + 1:] # teacher_name之后的列
                )
                
                # 将结果分解为两列
                df['first_name'] = names_split.apply(lambda x: x[0])
                df['last_name'] = names_split.apply(lambda x: x[1])
                
                # 重新排列列的顺序
                df = df[new_columns]
                
                logger.info(f"成功添加first_name和last_name列到teacher_name列后")
                all_dfs.append(df)
            except Exception as e:
                logger.error(f"处理文件 {file.name} 时出错: {str(e)}")
                continue

        if not all_dfs:
            raise ValueError("没有成功读取任何Excel文件")

        # 合并所有数据框
        merged_df = pd.concat(all_dfs, ignore_index=True)
        
        # 应用过滤条件（如果有）
        if filter_conditions:
            logger.info("正在应用过滤条件...")
            original_count = len(merged_df)
            merged_df = filter_dataframe(merged_df, filter_conditions)
            filtered_count = len(merged_df)
            logger.info(f"过滤前行数: {original_count}, 过滤后行数: {filtered_count}")
            
        # 应用排除条件（如果有）
        if exclude_conditions:
            logger.info("正在应用排除条件...")
            original_count = len(merged_df)
            merged_df = exclude_by_values(merged_df, exclude_conditions)
            filtered_count = len(merged_df)
            logger.info(f"排除前行数: {original_count}, 排除后行数: {filtered_count}")
            
        # 去除重复的teacher_name
        logger.info("正在处理重复的teacher_name...")
        merged_df = remove_duplicates_by_name(merged_df)
        
        # 准备输出文件路径
        if not output_name.endswith(('.xlsx', '.xls')):
            output_name += '.xlsx'
        output_path = data_dir / output_name
        
        # 保存合并后的文件
        merged_df.to_excel(output_path, index=False)
        logger.info(f"合并完成，已保存到: {output_path}")
        
        # 输出统计信息
        logger.info(f"合并后的文件包含 {len(merged_df)} 行数据")
        logger.info(f"列名: {', '.join(merged_df.columns.tolist())}")

        return str(output_path)

    except Exception as e:
        logger.error(f"合并过程中出错: {str(e)}")
        raise

if __name__ == "__main__":
    # 打印路径信息以验证
    logger.info(f"当前脚本目录: {current_dir}")
    logger.info(f"项目根目录: {root_dir}")
    logger.info(f"data目录: {Path(root_dir) / 'data'}")

    # 定义过滤条件示例
    filter_conditions = {
        'major_paper1_domain': {
            'values': ['生物科学类', '基础医学类', '生物医学工程类'],
            'match_type': 'any'  # 匹配任意一个值
        }
    }
    
    # 定义排除条件示例
    exclude_conditions = {
        'normalized_title': {
            'values': ['副教授', '高级讲师', '讲师'],
            'match_type': 'any'  # 匹配任意一个值就排除
        },
    }

    merge_excel_files(
        file_names=["机器人工程（人才领域-机器人工程）(1).xlsx", "机器人工程（算法匹配-机器人）_filtered.xlsx"],
        output_name="机器人（已合并过滤）",
        # filter_conditions=filter_conditions,
        exclude_conditions=exclude_conditions
    )