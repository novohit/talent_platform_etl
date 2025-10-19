import pandas as pd
import json
from datetime import datetime
import os
import requests
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
from functools import partial

@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model_name: str
    
    def get_completion(self, prompt: str) -> Optional[str]:
        """调用大模型API获取结果"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"API调用失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return None

def clean_text(text):
    """清理文本数据，移除特殊字符并处理None值"""
    if pd.isna(text) or text is None or text == '':
        return ''
    return str(text).strip()

def parse_json_field(field):
    """解析JSON格式的字段"""
    if pd.isna(field) or not field:
        return []
    try:
        if isinstance(field, str):
            return json.loads(field)
        return field
    except:
        return []

def format_experience(exp):
    """格式化工作经验"""
    experiences = parse_json_field(exp)
    if not experiences:
        return ''
    
    formatted_exp = []
    for e in experiences:
        company = e.get('company', '')
        title = e.get('title', '')
        date_range = f"{e.get('starts_at', '')} - {e.get('ends_at', '')}"
        formatted_exp.append(f"{company} | {title} | {date_range}")
    
    return '\n'.join(formatted_exp)

def format_education(edu):
    """格式化教育经历"""
    educations = parse_json_field(edu)
    if not educations:
        return ''
    
    formatted_edu = []
    for e in educations:
        school = e.get('school', '')
        degree = e.get('degree', '')
        field = e.get('field_of_study', '')
        date_range = f"{e.get('starts_at', '')} - {e.get('ends_at', '')}"
        formatted_edu.append(f"{school} | {degree} {field} | {date_range}")
    
    return '\n'.join(formatted_edu)

def enhance_basic_info(llm: LLMConfig, info: Dict) -> Dict:
    """处理基本个人信息"""
    if not info:
        return {}
    
    prompt = f"""请分析以下LinkedIn用户基本信息，提取关键信息并规范化格式：

    姓名: {info.get('name', '')}
    位置: {info.get('city', '')}, {info.get('country_code', '')}
    当前职位: {info.get('position', '')}
    当前公司: {info.get('current_company_name', '')}
    个人简介: {info.get('about', '')}

    请以JSON格式返回以下信息：
    1. normalized_name: 规范化的中文姓名（如果是外文名，保留原名并添加中文翻译）
    2. location: 规范化的地理位置（城市+国家，统一使用中文）
    3. current_position: 规范化的职位名称（中文）
    4. company_info: 当前公司信息（公司名称+简要描述）
    5. professional_summary: 优化后的个人简介（中文）
    
    直接返回JSON，不要包含其他解释。"""
    
    result = llm.get_completion(prompt)
    try:
        return json.loads(result) if result else {}
    except:
        return {}

def enhance_experience_info(llm: LLMConfig, experience: Dict) -> Dict:
    """处理工作经验信息"""
    if not experience:
        return {}
    
    exp_str = json.dumps(experience, ensure_ascii=False)
    prompt = f"""请分析以下工作经验信息，提取关键信息并规范化格式：

    {exp_str}

    请以JSON格式返回以下信息：
    1. company_history: 工作经历列表，每条包含：
       - company_name: 公司名称（中文优先）
       - position: 职位名称（中文）
       - duration: 工作时长
       - responsibilities: 主要职责（要点列表）
       - achievements: 主要成就（要点列表）
    2. skills_summary: 根据工作经历总结的技能列表
    3. industry_experience: 行业经验总结
    
    直接返回JSON，不要包含其他解释。"""
    
    result = llm.get_completion(prompt)
    try:
        return json.loads(result) if result else {}
    except:
        return {}

def enhance_education_info(llm: LLMConfig, education: Dict) -> Dict:
    """处理教育背景信息"""
    if not education:
        return {}
    
    edu_str = json.dumps(education, ensure_ascii=False)
    prompt = f"""请分析以下教育经历信息，提取关键信息并规范化格式：

    {edu_str}

    请以JSON格式返回以下信息：
    1. education_history: 教育经历列表，每条包含：
       - school: 学校名称（中文优先，附英文名）
       - degree: 学位（规范化的中文描述）
       - major: 专业（规范化的中文描述）
       - period: 就读时间
       - achievements: 主要成就或荣誉
    2. highest_degree: 最高学历信息
    3. academic_focus: 学术研究方向
    
    直接返回JSON，不要包含其他解释。"""
    
    result = llm.get_completion(prompt)
    try:
        return json.loads(result) if result else {}
    except:
        return {}

def enhance_achievements_info(llm: LLMConfig, info: Dict) -> Dict:
    """处理成就和专业技能信息"""
    if not info:
        return {}
    
    achievements_str = f"""
    证书: {info.get('certifications', [])}
    发表文章: {info.get('publications', [])}
    专利: {info.get('patents', [])}
    项目: {info.get('projects', [])}
    荣誉奖项: {info.get('honors_and_awards', [])}
    """
    
    prompt = f"""请分析以下专业成就信息，提取关键信息并规范化格式：

    {achievements_str}

    请以JSON格式返回以下信息：
    1. certifications: 专业证书列表（规范化的中文描述）
    2. publications: 发表文章列表，包含标题、发表时间、期刊/会议
    3. patents: 专利列表，包含专利名称、专利号、状态
    4. key_projects: 重要项目经历，包含项目名称、角色、技术栈
    5. honors: 荣誉奖项列表（规范化的中文描述）
    6. expertise_areas: 根据以上信息总结的专业领域
    
    直接返回JSON，不要包含其他解释。"""
    
    result = llm.get_completion(prompt)
    try:
        return json.loads(result) if result else {}
    except:
        return {}

def process_row(row: pd.Series, llm: LLMConfig) -> Dict:
    """处理单行数据"""
    try:
        # 1. 处理基本信息
        basic_info = {
            'name': clean_text(row['name']),
            'city': clean_text(row['city']),
            'country_code': clean_text(row['country_code']),
            'position': clean_text(row['position']),
            'about': clean_text(row['about']),
            'current_company_name': clean_text(row['current_company_name'])
        }
        enhanced_basic = enhance_basic_info(llm, basic_info)
        
        # 2. 处理工作经验
        experience_data = parse_json_field(row['experience'])
        enhanced_experience = enhance_experience_info(llm, experience_data)
        
        # 3. 处理教育背景
        education_data = parse_json_field(row['educations_details'])
        enhanced_education = enhance_education_info(llm, education_data)
        
        # 4. 处理成就和技能
        achievements_data = {
            'certifications': parse_json_field(row['certifications']),
            'publications': parse_json_field(row['publications']),
            'patents': parse_json_field(row['patents']),
            'projects': parse_json_field(row['projects']),
            'honors_and_awards': parse_json_field(row['honors_and_awards'])
        }
        enhanced_achievements = enhance_achievements_info(llm, achievements_data)
        
        # 5. 整合所有信息
        result = {
            # 基本信息
            'normalized_name': enhanced_basic.get('normalized_name', ''),
            'location': enhanced_basic.get('location', ''),
            'current_position': enhanced_basic.get('current_position', ''),
            'company_info': enhanced_basic.get('company_info', ''),
            'professional_summary': enhanced_basic.get('professional_summary', ''),
            
            # 工作经验
            'company_history': enhanced_experience.get('company_history', []),
            'skills_summary': enhanced_experience.get('skills_summary', []),
            'industry_experience': enhanced_experience.get('industry_experience', ''),
            
            # 教育背景
            'education_history': enhanced_education.get('education_history', []),
            'highest_degree': enhanced_education.get('highest_degree', ''),
            'academic_focus': enhanced_education.get('academic_focus', ''),
            
            # 成就和技能
            'certifications': enhanced_achievements.get('certifications', []),
            'publications': enhanced_achievements.get('publications', []),
            'patents': enhanced_achievements.get('patents', []),
            'key_projects': enhanced_achievements.get('key_projects', []),
            'honors': enhanced_achievements.get('honors', []),
            'expertise_areas': enhanced_achievements.get('expertise_areas', []),
            
            # 其他信息
            'languages': [lang.get('name', '') for lang in parse_json_field(row['languages'])],
            'connections_count': row['connections'],
            'volunteer_experience': parse_json_field(row['volunteer_experience']),
            'profile_url': clean_text(row['url'])
        }
        return result
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return None

def process_chunk(chunk: pd.DataFrame, llm: LLMConfig, pbar: tqdm) -> List[Dict]:
    """处理数据块"""
    results = []
    for _, row in chunk.iterrows():
        result = process_row(row, llm)
        if result:
            results.append(result)
        pbar.update(1)
    return results

def process_linkedin_data(input_file: str, output_file: str, num_threads: int = 4, chunk_size: int = 10):
    """处理LinkedIn数据"""
    print(f"开始处理文件: {input_file}")
    
    # 初始化大模型
    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"
    llm = LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)
    
    # 读取CSV文件
    df = pd.read_csv(input_file)
    total_rows = len(df)
    print(f"总共读取 {total_rows} 条记录")
    
    # 将数据分成小块
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
    print(f"数据已分成 {len(chunks)} 个块进行处理")
    
    # 创建进度条
    pbar = tqdm(total=total_rows, desc="处理进度")
    
    # 使用线程池处理数据
    all_results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 创建任务
        process_chunk_with_params = partial(process_chunk, llm=llm, pbar=pbar)
        future_to_chunk = {executor.submit(process_chunk_with_params, chunk): i for i, chunk in enumerate(chunks)}
        
        # 收集结果
        for future in as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                results = future.result()
                all_results.extend(results)
                print(f"块 {chunk_idx + 1}/{len(chunks)} 处理完成")
            except Exception as e:
                print(f"处理块 {chunk_idx} 时出错: {str(e)}")
    
    pbar.close()
    print("所有数据处理完成，正在保存结果...")
    
    # 将结果转换为DataFrame
    result_df = pd.DataFrame(all_results)
    
    # 保存处理后的数据
    result_df.to_excel(output_file, index=False)
    print(f"处理完成，结果已保存至: {output_file}")
    
    # 输出统计信息
    print(f"\n处理统计:")
    print(f"总记录数: {total_rows}")
    print(f"成功处理: {len(all_results)}")
    print(f"失败记录: {total_rows - len(all_results)}")

if __name__ == "__main__":
    input_file = "data/bd_20250901_093139_0.csv"
    output_file = "output/linkedin_data_processed.xlsx"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 使用4个线程，每个块10条记录
    process_linkedin_data(input_file, output_file, num_threads=16, chunk_size=10)

if __name__ == "__main__":
    input_file = "data/bd_20250901_093139_0.csv"
    output_file = "output/linkedin_data_processed.xlsx"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    process_linkedin_data(input_file, output_file)
