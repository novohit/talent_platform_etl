import pandas as pd
import os

def filter_affiliations(input_file):
    # 读取Excel文件
    df = pd.read_excel(input_file)
    
    # 过滤掉包含university或school的机构名称（不区分大小写）
    filtered_df = df[~df['机构名称'].str.lower().str.contains('university|school|universite|univeristy|universidade|college|大学|sciences|universitat|universiti|universitas|univesity|unversity|hospital|hopital|universidad|center|academy|institute|national|education|department', na=False)]
    
    # 重新计算排名
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df['排名'] = filtered_df.index + 1
    
    # 生成输出文件名
    file_name, file_ext = os.path.splitext(input_file)
    output_file = f"{file_name}_filtered{file_ext}"
    
    # 保存为Excel文件
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='机构统计')
        
        # 获取工作表对象
        worksheet = writer.sheets['机构统计']
        
        # 调整列宽
        worksheet.column_dimensions['A'].width = 8  # 排名
        worksheet.column_dimensions['B'].width = 50  # 机构名称
        worksheet.column_dimensions['C'].width = 12  # 出现次数
    
    print(f"原始数据行数: {len(df)}")
    print(f"过滤后数据行数: {len(filtered_df)}")
    print(f"已过滤掉 {len(df) - len(filtered_df)} 个包含university或school的机构")
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    input_file = "data/affiliations_analysis_20250902_154257.xlsx"
    filter_affiliations(input_file)
