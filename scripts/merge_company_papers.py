import os
import pandas as pd
from pathlib import Path
from talent_platform.logger import logger

def merge_excel_files(input_dir: str, output_file: str):
    """
    合并指定目录下的所有Excel文件
    
    Args:
        input_dir: 输入目录路径
        output_file: 输出文件路径
    """
    try:
        # 确保输入目录存在
        if not os.path.exists(input_dir):
            logger.error(f"输入目录不存在: {input_dir}")
            return
            
        # 获取所有Excel文件
        excel_files = list(Path(input_dir).glob("*_papers_authors.xlsx"))
        if not excel_files:
            logger.error(f"目录中没有找到Excel文件: {input_dir}")
            return
            
        logger.info(f"找到 {len(excel_files)} 个Excel文件")
        
        # 读取所有Excel文件
        all_data = []
        for file in excel_files:
            try:
                # 从文件名中提取公司名称
                company = file.stem.split('_papers_authors')[0]
                
                # 读取Excel文件
                df = pd.read_excel(file)
                
                # 添加来源文件信息
                df['来源文件'] = file.name
                
                # 确保所有必要的列都存在
                required_columns = ['论文ID', '论文标题', '作者', '机构简称', '机构完整名', '其他机构']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                logger.info(f"处理文件 {file.name}，包含 {len(df)} 条记录")
                all_data.append(df)
                
            except Exception as e:
                logger.error(f"处理文件 {file} 时出错: {str(e)}")
                continue
        
        if not all_data:
            logger.error("没有成功读取任何数据")
            return
            
        # 合并所有数据
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存合并后的数据
        merged_df.to_excel(output_file, index=False)
        logger.info(f"合并完成，共 {len(merged_df)} 条记录")
        logger.info(f"结果已保存到: {output_file}")
        
        # 显示每个机构的记录数量
        company_counts = merged_df['机构简称'].value_counts()
        logger.info("\n各机构记录数量:")
        for company, count in company_counts.items():
            logger.info(f"{company}: {count} 条记录")
        
    except Exception as e:
        logger.error(f"合并过程中发生错误: {str(e)}")


if __name__ == "__main__":
    # 设置输入输出路径
    INPUT_DIR = "output/power"
    OUTPUT_FILE = "output/merged_company_papers.xlsx"
    
    # 执行合并
    merge_excel_files(INPUT_DIR, OUTPUT_FILE)
