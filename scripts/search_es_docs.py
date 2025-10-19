from talent_platform.es.client import es_client
import pandas as pd
import os

def process_paper_data(paper, target_affiliation):
    """
    处理单篇论文数据，返回作者和机构的对应关系
    
    Args:
        paper: 论文数据
        target_affiliation: 目标机构名称（搜索词）
    """
    authors = paper.get("author_list", "").strip().split(";")
    affiliations = paper.get("affiliations", "").strip().split(";")
    
    # 清理数据
    authors = [a.strip() for a in authors if a.strip()]
    affiliations = [a.strip() for a in affiliations if a.strip()]
    
    # 如果机构为空或作者为空，返回None
    if not authors or not affiliations:
        return None
        
    # 情况1：如果机构只有一个，检查是否与目标机构匹配
    if len(affiliations) == 1:
        if target_affiliation.lower() in affiliations[0].lower():
            return [(author, affiliations[0]) for author in authors]
        return None
    
    # 情况2：检查所有机构是否相同且与目标机构匹配
    unique_affiliations = set(affiliations)
    if len(unique_affiliations) == 1 and target_affiliation.lower() in affiliations[0].lower():
        return [(author, affiliations[0]) for author in authors]
    
    # 情况3：如果作者数量和机构数量相同，只保留目标机构的作者
    if len(authors) == len(affiliations):
        matched_pairs = []
        for author, affiliation in zip(authors, affiliations):
            if target_affiliation.lower() in affiliation.lower():
                matched_pairs.append((author, affiliation))
        return matched_pairs if matched_pairs else None
    
    # 其他情况返回None
    return None

def search_affiliations(index: str, affiliation: str, size: int = 100):
    """
    搜索机构名称包含特定词的论文，并保存结果
    
    Args:
        index: 索引名称
        affiliation: 要搜索的机构名称
        size: 返回结果数量
    """
    # 构建查询
    query = {
        "match": {
            "affiliations": affiliation
        }
    }

    try:
        # 初始化scroll搜索
        results = es_client.client.search(
            index=index,
            body={
                "query": query,
                "size": 1000  # 每批次获取1000条数据
            },
            scroll="5m"  # 设置scroll上下文保持5分钟
        )
        
        # 获取第一批结果和scroll_id
        scroll_id = results["_scroll_id"]
        total_hits = results["hits"]["total"]["value"]
        print(f"\n包含机构 '{affiliation}' 的论文数量: {total_hits}")
        
        # 用于存储处理后的数据
        processed_data = []
        skipped_papers = []
        processed_count = 0
        
        # 处理所有批次的数据
        while True:
            # 处理当前批次
            hits = results["hits"]["hits"]
            if not hits:
                break
                
            for hit in hits:
                source = hit["_source"]
                paper_id = hit["_id"]
                processed_count += 1
                
                # 处理作者和机构对应关系
                author_affiliation_pairs = process_paper_data(source, affiliation)
                
                if author_affiliation_pairs:
                    # 为每个作者-机构对添加论文信息
                    for author, author_affiliation in author_affiliation_pairs:
                        processed_data.append({
                            "paper_id": paper_id,
                            "title": source.get("title", ""),
                            "author": author,
                            "affiliation": author_affiliation,
                            "publication_date": source.get("publication_date", ""),
                            "doi": source.get("doi", "")
                        })
                else:
                    # 记录无法处理的论文
                    skipped_papers.append({
                        "paper_id": paper_id,
                        "title": source.get("title", ""),
                        "author_list": source.get("author_list", ""),
                        "affiliations": source.get("affiliations", ""),
                        "reason": "作者数量与机构数量不匹配"
                    })
                
                if processed_count % 1000 == 0:
                    print(f"已处理 {processed_count}/{total_hits} 条数据...")
            
            # 获取下一批数据
            results = es_client.client.scroll(
                scroll_id=scroll_id,
                scroll="5m"
            )
            
        # 清理scroll
        es_client.client.clear_scroll(scroll_id=scroll_id)
        
        # 保存处理后的数据
        if processed_data:
            df = pd.DataFrame(processed_data)
            output_file = os.path.join("output", f"{affiliation}_papers_processed.xlsx")
            df.to_excel(output_file, index=False)
            print(f"\n成功处理的数据已保存到: {output_file}")
            print(f"共处理 {len(processed_data)} 条作者-机构对应关系")
        
        # 保存无法处理的数据
        if skipped_papers:
            df_skipped = pd.DataFrame(skipped_papers)
            skip_file = os.path.join("output", f"{affiliation}_papers_skipped.xlsx")
            df_skipped.to_excel(skip_file, index=False)
            print(f"无法处理的论文数据已保存到: {skip_file}")
            print(f"共有 {len(skipped_papers)} 篇论文无法确定作者-机构对应关系")
        
        # 保存处理后的数据
        if processed_data:
            df = pd.DataFrame(processed_data)
            output_file = os.path.join("output", f"{affiliation}_papers_processed.xlsx")
            df.to_excel(output_file, index=False)
            print(f"\n成功处理的数据已保存到: {output_file}")
            print(f"共处理 {len(processed_data)} 条作者-机构对应关系")
        
        # 保存无法处理的数据
        if skipped_papers:
            df_skipped = pd.DataFrame(skipped_papers)
            skip_file = os.path.join("output", f"{affiliation}_papers_skipped.xlsx")
            df_skipped.to_excel(skip_file, index=False)
            print(f"无法处理的论文数据已保存到: {skip_file}")
            print(f"共有 {len(skipped_papers)} 篇论文无法确定作者-机构对应关系")
            
    except Exception as e:
        print(f"搜索或处理数据时出错: {str(e)}")

if __name__ == "__main__":
    # 示例：搜索包含特定机构的论文
    search_affiliations(
        index="raw_teacher_paper",  # 论文索引
        affiliation="meituan"  
    )
