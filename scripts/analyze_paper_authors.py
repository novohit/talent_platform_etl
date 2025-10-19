import pandas as pd
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from talent_platform.es import es_client
import json
import requests

# ES配置
INDEX_NAME = "raw_teacher_paper"
BATCH_SIZE = 1000  # ES查询批次大小

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
                {"role": "system", "content": "你是一个专业的论文作者分析助手，帮助分析作者的单位类型。"},
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

def read_relevant_journals() -> List[str]:
    """读取重点期刊列表"""
    journals = []
    try:
        with open('data/重点期刊.txt', 'r', encoding='utf-8') as f:
            journals = [line.strip() for line in f if line.strip()]
        return journals
    except Exception as e:
        print(f"Error reading journals file: {e}")
        return []

def analyze_authors(llm: LLMConfig, affiliations: str, author_list: str) -> Dict:
    """分析作者的单位类型"""
    try:
        # 将作者和单位信息组合成结构化文本
        authors = author_list.split(';')
        affils = affiliations.split(';')
        
        # 确保长度匹配
        min_len = min(len(authors), len(affils))
        author_info = []
        for i in range(min_len):
            author_info.append({
                "author": authors[i].strip(),
                "affiliation": affils[i].strip()
            })
            
        prompt = f"""
        请分析以下作者的单位信息，识别出在企业工作的作者。

        判断标准：
        1. 采用排除法，只要不能明确识别为高校或研究所或科研协会或政府机构或科研协会的单位，就视为可能的企业单位
        2. 对于不确定的情况，请先分析机构名称，如果机构名称倾向于判定为企业，则判定为企业

        请用JSON格式回答，格式如下：
        {{
            "enterprise_authors": [
                {{
                    "author": "作者名",
                    "affiliation": "单位名"
                }}
            ]
        }}
        """
        
        # 将作者信息转换为文本
        text = "作者及其单位信息:\n"
        for info in author_info:
            text += f"作者: {info['author']}, 单位: {info['affiliation']}\n"
        
        # 调用大模型分析
        result = llm.analyze_text(text, prompt)
        try:
            return json.loads(result)
        except:
            return {"enterprise_authors": []}
            
    except Exception as e:
        print(f"Error analyzing authors: {e}")
        return {"enterprise_authors": []}

def fetch_papers_for_journal(journal_name: str) -> List[Dict]:
    """从ES获取单个期刊的论文信息，使用scroll API"""
    try:
        query = {
            "bool": {
                "must": [
                    {"match": {"paper_source": journal_name}}
                ]
            }
        }
        
        source = [
            "id",
            "title",
            "paper_source",
            "affiliations",
            "author_list"
        ]
        
        # 初始化scroll
        result = es_client.client.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "_source": source,
                "size": BATCH_SIZE
            },
            scroll='5m'
        )
        
        papers = []
        # 获取第一批数据
        hits = result.get("hits", {}).get("hits", [])
        for hit in hits:
            paper = hit["_source"]
            if paper.get("affiliations") and paper.get("author_list"):
                papers.append(paper)
        
        scroll_id = result.get('_scroll_id')
        total_hits = result.get("hits", {}).get("total", {}).get("value", 0)
        
        print(f"开始获取 {journal_name} 的论文，预计总数: {total_hits}")
        
        # 继续scroll直到没有更多数据
        while True:
            if not scroll_id:
                break
                
            result = es_client.client.scroll(
                scroll_id=scroll_id,
                scroll='5m'
            )
            
            # 获取这一批的数据
            hits = result.get("hits", {}).get("hits", [])
            if not hits:
                break
                
            for hit in hits:
                paper = hit["_source"]
                if paper.get("affiliations") and paper.get("author_list"):
                    papers.append(paper)
            
            scroll_id = result.get('_scroll_id')
            print(f"已获取 {journal_name} 的 {len(papers)}/{total_hits} 篇论文")
            
        # 清理scroll
        if scroll_id:
            try:
                es_client.client.clear_scroll(scroll_id=scroll_id)
            except:
                pass
                
        return papers
    except Exception as e:
        print(f"Error fetching papers for journal {journal_name} from ES: {e}")
        return []

def process_journal_batch(journal_names: List[str]) -> List[Dict]:
    """处理一批期刊的论文"""
    all_papers = []
    for journal_name in journal_names:
        papers = fetch_papers_for_journal(journal_name)
        all_papers.extend(papers)
    return all_papers

def load_analyzed_ids() -> set:
    """加载已经分析过的论文ID"""
    analyzed_ids = set()
    try:
        with open('output/analyzed_paper_ids.txt', 'r') as f:
            for line in f:
                analyzed_ids.add(line.strip())
    except FileNotFoundError:
        pass
    return analyzed_ids

def save_analyzed_id(paper_id: str):
    """保存已分析的论文ID"""
    with open('output/analyzed_paper_ids.txt', 'a') as f:
        f.write(f"{str(paper_id)}\n")  # 确保ID保存为字符串格式

def ensure_csv_headers():
    """确保CSV文件存在并包含表头"""
    csv_path = 'output/enterprise_papers.csv'
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow([
                '论文ID',
                '标题',
                '来源期刊',
                '作者姓名',
                '企业单位',
                '完整单位信息'
            ])

def save_enterprise_paper(paper: Dict):
    """保存包含企业作者的论文信息到CSV"""
    ensure_csv_headers()
    
    # 准备CSV行数据
    csv_rows = []
    for author in paper['enterprise_authors']:
        # 获取完整单位信息
        all_affils = ""
        if paper.get('affiliations') and paper.get('author_list'):
            try:
                author_index = paper['author_list'].split(';').index(author['author'].strip())
                all_affils = paper['affiliations'].split(';')[author_index].strip()
            except (ValueError, IndexError):
                all_affils = "无法获取完整单位信息"
        
        # 构建CSV行
        row = [
            paper['id'],
            paper['title'],
            paper['paper_source'],
            author['author'],
            author['affiliation'],
            all_affils
        ]
        csv_rows.append(row)
    
    # 写入CSV文件
    with open('output/enterprise_papers.csv', 'a', encoding='utf-8', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    
    # 同时打印到控制台
    print(f"\n发现企业作者论文: {paper['title']}")
    print(f"来源: {paper['paper_source']}")
    print(f"企业作者: {[a['author'] for a in paper['enterprise_authors']]}")

def analyze_papers_batch(papers: List[Dict], llm: LLMConfig, pbar: tqdm, analyzed_ids: set) -> List[Dict]:
    """分析一批论文的作者信息"""
    analyzed_papers = []
    for paper in papers:
        # 检查是否已经分析过
        if paper['id'] in analyzed_ids:
            pbar.update(1)
            continue
            
        analysis = analyze_authors(llm, paper["affiliations"], paper["author_list"])
        if analysis.get("enterprise_authors"):
            paper["enterprise_authors"] = analysis["enterprise_authors"]
            analyzed_papers.append(paper)
            # 实时保存和输出结果
            save_enterprise_paper(paper)
            
        # 记录已分析的ID
        save_analyzed_id(paper['id'])
        pbar.update(1)
    return analyzed_papers

def analyze_all_papers():
    """分析所有期刊论文中的企业作者"""
    # 初始化大模型
    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"
    llm = LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)
    
    # 读取期刊列表
    journal_names = read_relevant_journals()
    if not journal_names:
        print("No journals found in the file")
        return
    
    try:
        total_journals = len(journal_names)
        print(f"\n开始从 {total_journals} 个期刊获取论文...")
        
        # 第一阶段：获取所有论文
        all_papers = []
        batch_size = 3  # 每个批次处理的期刊数量
        
        # 将期刊分成批次
        journal_batches = [
            journal_names[i:i + batch_size] 
            for i in range(0, len(journal_names), batch_size)
        ]
        
        # 使用线程池并行获取论文
        with ThreadPoolExecutor(max_workers=12) as executor:
            future_to_batch = {
                executor.submit(process_journal_batch, batch): batch
                for batch in journal_batches
            }
            
            with tqdm(total=len(journal_batches), desc="获取论文进度") as pbar:
                for future in as_completed(future_to_batch):
                    try:
                        batch_papers = future.result()
                        all_papers.extend(batch_papers)
                    except Exception as e:
                        print(f"获取论文批次时发生错误: {e}")
                    pbar.update(1)
        
        print(f"\n共获取到 {len(all_papers)} 篇论文")
        print("\n开始分析论文作者信息...")
        
        # 第二阶段：分析论文作者
        print("\n加载已分析的论文ID...")
        analyzed_ids = load_analyzed_ids()
        print(f"已有 {len(analyzed_ids)} 篇论文被分析过")
        
        # 过滤掉已经分析过的论文
        papers_to_analyze = []
        skipped_count = 0
        for paper in all_papers:
            if str(paper['id']) not in analyzed_ids:  # 确保ID转换为字符串进行比较
                papers_to_analyze.append(paper)
            else:
                skipped_count += 1
        
        print(f"跳过已分析的 {skipped_count} 篇论文")
        print(f"本次需要分析 {len(papers_to_analyze)} 篇论文")
        
        analyzed_papers = []
        analysis_batch_size = 50  # 每个批次分析的论文数量
        
        # 将论文分成批次
        paper_batches = [
            papers_to_analyze[i:i + analysis_batch_size]
            for i in range(0, len(papers_to_analyze), analysis_batch_size)
        ]
        
        # 使用线程池并行分析论文
        with ThreadPoolExecutor(max_workers=12) as executor:
            with tqdm(total=len(papers_to_analyze), desc="分析作者进度") as pbar:
                futures = []
                for batch in paper_batches:
                    future = executor.submit(analyze_papers_batch, batch, llm, pbar, analyzed_ids)
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        batch_results = future.result()
                        analyzed_papers.extend(batch_results)
                    except Exception as e:
                        print(f"分析论文批次时发生错误: {e}")
        
        # 转换为DataFrame
        papers_df = pd.DataFrame(all_papers)
        
        # 保存结果到Excel
        output_path = os.path.join('output', 'enterprise_authors_papers.xlsx')
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 写入所有论文
            papers_df.to_excel(writer, sheet_name='包含企业作者的论文', index=False)
            
            # 统计每个期刊的企业作者论文数量
            journal_stats = papers_df.groupby('paper_source').size().reset_index(name='论文数量')
            journal_stats = journal_stats.sort_values('论文数量', ascending=False)
            journal_stats.to_excel(writer, sheet_name='期刊统计', index=False)
            
            # 提取所有企业作者信息
            enterprise_authors = []
            for _, row in papers_df.iterrows():
                if isinstance(row['enterprise_authors'], list):
                    for author in row['enterprise_authors']:
                        enterprise_authors.append({
                            'paper_title': row['title'],
                            'paper_source': row['paper_source'],
                            'author': author['author'],
                            'affiliation': author['affiliation'],
                            'reason': author.get('reason', '')
                        })
            
            # 保存企业作者明细
            authors_df = pd.DataFrame(enterprise_authors)
            authors_df.to_excel(writer, sheet_name='企业作者明细', index=False)
        
        print(f"\n数据已保存到: {output_path}")
        print(f"总共找到 {len(papers_df)} 篇包含企业作者的论文")
        print(f"总共找到 {len(enterprise_authors)} 位企业作者")
        
        return papers_df
        
    except Exception as e:
        print(f"Error in main process: {e}")
        return None

if __name__ == "__main__":
    analyze_all_papers()
