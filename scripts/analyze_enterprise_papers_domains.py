import pandas as pd
import os
from typing import List, Dict
import json
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

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
                {"role": "system", "content": "你是一个专业的论文分析助手，帮助分析论文是否与特定技术领域相关。"},
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
        return domains
    except Exception as e:
        print(f"Error reading domains file: {e}")
        return []

def analyze_paper_batch(papers: List[Dict], llm: LLMConfig, domains: List[str]) -> List[Dict]:
    """分析一批论文是否与重点领域相关"""
    results = []
    for paper in papers:
        paper_text = f"""
        论文标题: {paper['标题']}
        企业单位: {paper['企业单位']}
        """
        
        prompt = f"""
        请分析这篇论文是否可能涉及以下任一重点技术领域：
        {', '.join(domains)}
        
        分析要求：
        1. 主要基于论文标题和企业单位进行判断
        2. 考虑企业的业务领域和论文主题的关联性
        3. 如果企业是电力相关企业，要特别关注与电力技术相关的领域
        4. 采用宽松的判断标准，只要有一定相关性就算
        
        请用JSON格式回答，格式如下：
        {{
            "contains_key_domain": true/false,
            "relevant_domains": ["领域1", "领域2"],
        }}
        """
        
        try:
            result = llm.analyze_text(paper_text, prompt)
            analysis = json.loads(result)
            paper.update({
                '包含重点领域': analysis['contains_key_domain'],
                '相关领域': ';'.join(analysis['relevant_domains']) if analysis['relevant_domains'] else ''
            })
        except Exception as e:
            print(f"Error analyzing paper {paper['标题']}: {e}")
            paper.update({
                '包含重点领域': False,
                '相关领域': ''
            })
        
        results.append(paper)
        
        # 打印发现的相关论文
        if paper['包含重点领域']:
            print(f"\n发现相关论文: {paper['标题']}")
            print(f"相关领域: {paper['相关领域']}")
            
    return results

def load_analyzed_papers() -> set:
    """加载已经分析过的论文ID和作者组合"""
    analyzed_pairs = set()
    try:
        output_file = 'data/enterprise_papers_with_domains.csv'
        if os.path.exists(output_file):
            df = pd.read_csv(output_file)
            # 使用论文ID和作者姓名的组合作为唯一标识
            analyzed_pairs = set(
                df.apply(lambda row: f"{row['论文ID']}_{row['作者姓名']}", axis=1)
            )
    except Exception as e:
        print(f"Error loading analyzed papers: {e}")
    return analyzed_pairs

def main():
    # 初始化大模型
    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"
    llm = LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)
    
    # 读取重点领域
    domains = read_key_domains()
    if not domains:
        print("Failed to read key domains")
        return
    
    # 读取企业论文数据
    print("读取企业论文数据...")
    df = pd.read_csv('data/enterprise_papers.csv')
    
    # 加载已分析的论文-作者对
    analyzed_pairs = load_analyzed_papers()
    print(f"已有 {len(analyzed_pairs)} 个论文-作者对被分析过")
    
    # 为每行创建唯一标识
    df['unique_id'] = df.apply(lambda row: f"{row['论文ID']}_{row['作者姓名']}", axis=1)
    
    # 过滤未分析的论文-作者对
    df_to_analyze = df[~df['unique_id'].isin(analyzed_pairs)].copy()
    print(f"本次需要分析 {len(df_to_analyze)} 个论文-作者对")
    
    # 删除临时列
    df_to_analyze = df_to_analyze.drop('unique_id', axis=1)
    
    # 准备结果文件
    output_file = 'data/enterprise_papers_with_domains.csv'
    
    # 如果文件不存在，写入表头
    if not os.path.exists(output_file):
        df_to_analyze.head(0).to_csv(output_file, index=False)
    
    # 分批处理论文
    batch_size = 10  # 每个批次的论文数量
    num_threads = 16  # 线程数量
    
    # 将论文分成批次
    paper_batches = []
    for i in range(0, len(df_to_analyze), batch_size):
        batch = df_to_analyze.iloc[i:i+batch_size].to_dict('records')
        paper_batches.append(batch)
    
    total_batches = len(paper_batches)
    print(f"\n使用 {num_threads} 个线程处理 {total_batches} 个批次...")
    
    # 使用线程池并行处理
    analyzed_papers = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交所有批次任务
        future_to_batch = {
            executor.submit(analyze_paper_batch, batch, llm, domains): batch
            for batch in paper_batches
        }
        
        # 使用tqdm显示进度
        with tqdm(total=total_batches, desc="分析进度") as pbar:
            for future in as_completed(future_to_batch):
                try:
                    # 获取分析结果
                    batch_results = future.result()
                    analyzed_papers.extend(batch_results)
                    
                    # 将这批结果保存到文件
                    batch_df = pd.DataFrame(batch_results)
                    batch_df.to_csv(output_file, mode='a', header=False, index=False)
                    
                except Exception as e:
                    print(f"\n处理批次时发生错误: {e}")
                
                pbar.update(1)
    
    print("\n分析完成！结果已保存到:", output_file)

if __name__ == "__main__":
    main()
