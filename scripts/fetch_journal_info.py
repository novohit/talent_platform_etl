import pymysql
from pymysql import Error
import pandas as pd
from dotenv import load_dotenv
import os
import json
import requests
from typing import List, Dict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # 添加进度条支持

class LLMConfig:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def analyze_text(self, text: str, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一个专业的期刊/会议分析助手，帮助分析期刊/会议内容是否包含特定技术领域。"},
                {"role": "user", "content": prompt + "\n" + text}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error in API call: {e}")
            return ""

def read_key_domains() -> List[str]:
    """读取重点领域列表"""
    domains = []
    try:
        with open('data/重点领域.txt', 'r', encoding='utf-8') as f:
            domains = [line.strip()[3:] for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading domains file: {e}")
    return domains

def get_db_connection():
    """Create database connection."""
    try:
        connection = pymysql.connect(
            host='172.22.121.11',
            port=43200,
            database='personnel-matching-new',
            user='zwx',
            password='006af022-f15c-442c-8c56-e71a45d4531e'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def analyze_journal(llm: LLMConfig, journal_info: Dict, domains: List[str]) -> Dict:
    """分析期刊信息是否包含重点领域技术"""
    journal_text = f"""
    期刊/会议名称: {journal_info['journal_name']}
    类别: {journal_info['category']}
    年份: {journal_info['year']}
    子类: {journal_info['subclass']}
    期刊/会议: {journal_info['Publication_category']}
    """
    
    prompt = f"""
    请分析这个期刊/会议的信息，判断它是否可能涉及以下任一南方电网重点技术领域：
    {', '.join(domains)}
    
    分析要求：
    1. 只要期刊/会议的范围、子类、主题等与某个领域有一定相关性，就认为可能包含该领域
    2. 考虑期刊/会议的交叉学科特性，可能同时涉及多个领域
    
    请用JSON格式回答，格式如下：
    {{
        "contains_key_domain": true/false,
        "relevant_domains": ["领域1", "领域2"]
    }}
    
    注意：只要有一定可能性包含某领域，就将其加入relevant_domains列表。
    """
    
    result = llm.analyze_text(journal_text, prompt)
    try:
        return json.loads(result)
    except:
        print(f"Error parsing LLM response for journal: {journal_info['journal_name']}")
        return {
            "contains_key_domain": False,
            "relevant_domains": [],
            "reasoning": "分析失败"
        }

def fetch_journal_info():
    """Fetch journal information from the database and analyze with LLM."""
    # 初始化翻译器
    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"
    llm = LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)
    
    # 读取重点领域
    domains = read_key_domains()
    if not domains:
        print("Failed to read key domains")
        return None
    
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        # Create a pandas DataFrame from the query
        query = """
        SELECT journal_name, category, `year`, subclass, Publication_category 
        FROM product_en_journal_info where category = '工程技术' OR category = '计算机科学' OR category is NULL OR category = '' OR category = '综合性期刊'
        """
        
        df = pd.read_sql(query, connection)
        
        # 使用线程池并行处理期刊分析
        results = []
        # 创建一个包含所有期刊信息的列表
        journal_infos = [row.to_dict() for _, row in df.iterrows()]
        total_journals = len(journal_infos)
        
        print(f"\n开始并行分析 {total_journals} 个期刊...")
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有任务
            future_to_journal = {
                executor.submit(analyze_journal, llm, journal_info, domains): journal_info
                for journal_info in journal_infos
            }
            
            # 使用tqdm创建进度条
            with tqdm(total=total_journals, desc="分析进度") as pbar:
                # 处理完成的任务
                for future in as_completed(future_to_journal):
                    journal_info = future_to_journal[future]
                    try:
                        analysis = future.result()
                        # 合并原始信息和分析结果
                        result_row = {**journal_info, **analysis}
                        results.append(result_row)
                    except Exception as e:
                        print(f"处理期刊时发生错误 {journal_info['journal_name']}: {e}")
                    pbar.update(1)  # 更新进度条
        
        # 创建新的DataFrame包含分析结果
        results_df = pd.DataFrame(results)
        
        # 保存结果到Excel
        output_path = os.path.join('output', 'journal_info_analyzed.xlsx')
        
        # 创建一个Excel写入器
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 写入主数据表
            results_df.to_excel(writer, sheet_name='所有期刊', index=False)
            
            # 写入包含重点领域的期刊到单独sheet
            relevant_journals = results_df[results_df['contains_key_domain'] == True]
            relevant_journals.to_excel(writer, sheet_name='包含重点领域', index=False)
            
            # 统计每个领域的期刊数量
            domain_stats = []
            for domain in domains:
                count = relevant_journals[relevant_journals['relevant_domains'].apply(
                    lambda x: domain in x if isinstance(x, list) else False
                )].shape[0]
                domain_stats.append({'领域': domain, '期刊数量': count})
            
            # 写入统计数据
            stats_df = pd.DataFrame(domain_stats)
            stats_df.to_excel(writer, sheet_name='领域统计', index=False)
        
        print(f"Data has been saved to {output_path}")
        print("\nFirst few rows of the analyzed data:")
        print(results_df.head())
        print("\nData shape:", results_df.shape)
        
        # 统计包含重点领域的期刊数量
        contains_key_domain = results_df[results_df['contains_key_domain'] == True]
        print(f"\nNumber of journals containing key domains: {len(contains_key_domain)}")
        
        return results_df
        
    except Error as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        connection.close()

if __name__ == "__main__":
    fetch_journal_info()