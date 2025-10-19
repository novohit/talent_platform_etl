import pandas as pd
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from talent_platform.es import es_client

# ES配置
INDEX_NAME = "raw_teacher_paper"
BATCH_SIZE = 1000  # ES查询批次大小

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
        
        # 定义要获取的字段
        source = [
            "id",
            "title",
            "paper_source",
            'affiliations',
            'author_list',
        ]
        
        # 初始化scroll
        result = es_client.client.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "_source": source,
                "size": BATCH_SIZE
            },
            scroll='5m'  # 设置scroll时间窗口
        )
        
        # 获取第一批数据
        papers = [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
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
            batch = [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
            if not batch:
                break
                
            papers.extend(batch)
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

def fetch_all_papers():
    """获取所有相关期刊的论文信息"""
    # 读取相关期刊信息
    journal_names = read_relevant_journals()
    if not journal_names:
        print("No journals found in the file")
        return
    
    try:
        total_journals = len(journal_names)
        print(f"\n开始获取 {total_journals} 个期刊的论文...")
        
        all_papers = []
        batch_size = 3  # 每个批次处理的期刊数量
        
        # 将期刊分成批次
        journal_batches = [
            journal_names[i:i + batch_size] 
            for i in range(0, len(journal_names), batch_size)
        ]
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(process_journal_batch, batch): batch
                for batch in journal_batches
            }
            
            # 使用tqdm创建进度条
            with tqdm(total=len(journal_batches), desc="处理进度") as pbar:
                for future in as_completed(future_to_batch):
                    try:
                        batch_papers = future.result()
                        all_papers.extend(batch_papers)
                    except Exception as e:
                        print(f"处理批次时发生错误: {e}")
                    pbar.update(1)
        
        # 转换为DataFrame
        papers_df = pd.DataFrame(all_papers)
        
        # 保存结果到Excel
        output_path = os.path.join('output', 'papers_from_key_journals.xlsx')
        
        # 创建Excel写入器
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 写入所有论文
            papers_df.to_excel(writer, sheet_name='所有论文', index=False)
            
            # 按期刊统计论文数量
            journal_stats = papers_df.groupby('paper_source').size().reset_index(name='论文数量')
            journal_stats = journal_stats.sort_values('论文数量', ascending=False)
            journal_stats.to_excel(writer, sheet_name='期刊统计', index=False)
            
            # 按年份统计论文数量
            if 'publish_date' in papers_df.columns:
                papers_df['year'] = pd.to_datetime(papers_df['publish_date']).dt.year
                year_stats = papers_df.groupby('year').size().reset_index(name='论文数量')
                year_stats = year_stats.sort_values('year', ascending=False)
                year_stats.to_excel(writer, sheet_name='年份统计', index=False)
        
        print(f"\n数据已保存到: {output_path}")
        print(f"总共获取到 {len(papers_df)} 篇论文")
        print("\n期刊论文数量统计:")
        print(journal_stats)
        
        return papers_df
        
    except Exception as e:
        print(f"Error in main process: {e}")
        return None

if __name__ == "__main__":
    fetch_all_papers()
