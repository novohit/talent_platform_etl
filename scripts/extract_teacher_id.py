import os
import re
from pathlib import Path

def extract_teacher_id_from_pdf(file_path):
    """
    从PDF文件中提取teacher_id
    :param file_path: PDF文件路径
    :return: teacher_id 或 None
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            
        # 使用正则表达式匹配URI中的UUID格式的teacher_id
        pattern = r'/talent/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern, content)
        
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return None

def process_pdf_files(directory):
    """
    处理目录下的所有PDF文件
    :param directory: 目录路径
    :return: 包含文件名和teacher_id的字典列表
    """
    results = []
    directory_path = Path(directory)
    
    for pdf_file in directory_path.glob('*.pdf'):
        teacher_id = extract_teacher_id_from_pdf(pdf_file)
        if teacher_id:
            results.append({
                'file_name': pdf_file.name,
                'teacher_id': teacher_id
            })
    
    return results

def save_results(results, output_file='output/pdf_teacher_ids.txt'):
    """
    保存结果到文件
    :param results: 结果列表
    :param output_file: 输出文件路径
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(f"文件名: {item['file_name']}\n")
            f.write(f"Teacher ID: {item['teacher_id']}\n")
            f.write('-' * 50 + '\n')

def main():
    # 获取当前工作目录
    current_dir = os.getcwd()
    
    # 处理PDF文件
    results = process_pdf_files(current_dir)
    
    if results:
        # 保存结果
        save_results(results)
        print(f"成功处理 {len(results)} 个文件")
        print("结果已保存到 output/pdf_teacher_ids.txt")
    else:
        print("未找到包含teacher_id的PDF文件")

if __name__ == '__main__':
    main() 