from talent_platform.es.client import es_client
from talent_platform.logger import logger
from talent_platform.db.database import get_session
from sqlmodel import text
import json
import re
import pandas as pd
from datetime import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from queue import Queue
from typing import List, Dict, Any

# 创建一个线程安全的计数器和结果列表
processed_count_lock = Lock()
results_lock = Lock()


def get_paper_addr_mapping(paper_id: int) -> str:
    """
    从数据库获取论文的addr_affi_mapping信息
    """
    with get_session() as session:
        query = text("SELECT addr_affi_mapping FROM raw_teacher_paper WHERE id = :id")
        result = session.execute(query, {"id": paper_id}).first()
        return result[0] if result else "N/A"


def parse_addresses(addresses: str) -> dict:
    """
    解析论文地址字符串，返回作者和其完整机构名的映射
    格式如：[Author1; Author2] Inst1; [Author3] Inst2
    注意：作者名可能包含逗号，如 [Wang, Hao; Li, Huiqi]
    如果同一作者出现在多个机构，会保存所有机构列表
    """
    author_inst_map = {}
    if not addresses:
        return author_inst_map
        
    
    # 使用正则表达式找到所有的 [...] institution 块
    address_blocks = re.findall(r'\[(.*?)\](.*?)(?=\[|$)', addresses)
    
    for authors_str, institution in address_blocks:
        # 清理字符串
        authors_str = authors_str.strip()
        institution = institution.strip(' ;')
        
        # 分割多个作者
        authors = [author.strip() for author in authors_str.split(';')]
        
        # 为每个作者建立映射
        for author in authors:
            if author:  # 确保不是空字符串
                if author in author_inst_map:
                    # 如果作者已存在，添加到机构列表
                    if isinstance(author_inst_map[author], list):
                        author_inst_map[author].append(institution)
                    else:
                        author_inst_map[author] = [author_inst_map[author], institution]
                else:
                    # 新作者，直接设置机构
                    author_inst_map[author] = institution
    
    return author_inst_map


def process_single_doc(doc_data: Dict[str, Any], search_term: str) -> List[Dict[str, Any]]:
    """
    处理单个文档，返回找到的目标公司相关作者信息
    """
    results = []
    try:
        hit = doc_data
        doc = hit["_source"]
        
        # 从数据库获取补充信息
        paper_id = int(hit['_id'])
        addr_mapping_str = get_paper_addr_mapping(paper_id)
        
        # 解析地址映射JSON
        addr_mapping = json.loads(addr_mapping_str) if addr_mapping_str != "N/A" else {}
        
        # 解析addresses获取作者-机构映射
        author_inst_map = parse_addresses(doc.get('addresses', ''))
        
        # 找出在目标公司/机构的作者
        target_authors = []
        for author, institutions in author_inst_map.items():
            # 处理单个机构或多个机构的情况
            inst_list = institutions if isinstance(institutions, list) else [institutions]
            
            target_institutions = []
            for inst in inst_list:
                # 检查这个完整机构名是否在addr_mapping中，并且映射到目标搜索词
                if inst in addr_mapping and addr_mapping[inst].lower() == search_term.lower():
                    target_institutions.append(inst)
            
            # 如果有目标公司相关的机构，添加到结果中
            if target_institutions:
                target_authors.append({
                    'name': author,
                    'target_institutions': target_institutions,
                    'all_institutions': inst_list
                })
        
        # 处理目标公司相关的作者信息
        if target_authors:
            for author_info in target_authors:
                # 记录到结果列表
                non_target_institutions = []
                if len(author_info['all_institutions']) > len(author_info['target_institutions']):
                    non_target_institutions = [inst for inst in author_info['all_institutions'] 
                                             if inst not in author_info['target_institutions']]
                
                result_row = {
                    '论文ID': hit['_id'],
                    '论文标题': doc.get('title', 'N/A'),
                    '作者': author_info['name'],
                    '机构简称': search_term,
                    '机构完整名': '; '.join(author_info['target_institutions']),
                    '其他机构': '; '.join(non_target_institutions) if non_target_institutions else '',
                }
                results.append(result_row)
                
    except Exception as e:
        logger.error(f"处理文档 {doc_data.get('_id')} 时出错: {str(e)}")
    
    return results


def search_company_papers(search_term: str = "tencent", batch_size: int = 100, save_to_excel: bool = True, max_workers: int = 10):
    """
    搜索指定公司/机构相关的论文，并解析出相关的作者-机构对应关系
    使用scroll API获取所有匹配的数据，使用多线程处理文档
    
    Args:
        search_term: 搜索的公司/机构名称（默认为tencent）
        batch_size: 每批次处理的文档数量（默认为100）
        save_to_excel: 是否保存到Excel文件（默认为True）
        max_workers: 最大线程数（默认为10）
    """
    # 用于存储所有结果的列表
    all_results = []
    processed_count = 0
    
    try:
        # 构建查询
        query = {
            "term": {
                "affiliations": search_term.lower()
            }
        }
        
        # 首次搜索，初始化scroll
        result = es_client.client.search(
            index="raw_teacher_paper",
            body={
                "query": query,
                "size": batch_size
            },
            scroll='2m'  # 保持scroll上下文2分钟
        )
        
        # 获取scroll_id
        scroll_id = result['_scroll_id']
        
        # 打印结果
        result_body = result.get('body', result) if 'body' in result else result
        total_hits = result_body.get("hits", {}).get("total", {}).get("value", 0)
        logger.info(f"搜索词: {search_term}")
        logger.info(f"找到 {total_hits} 条匹配的文档")
        logger.info(f"开始使用scroll API处理所有数据...")
        
        # 处理第一批数据
        hits = result_body.get("hits", {}).get("hits", [])
        
        while hits:
            logger.info(f"正在处理第 {processed_count + 1} - {processed_count + len(hits)} 条文档...")
            
            # 使用线程池并行处理当前批次的文档
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_doc = {
                    executor.submit(process_single_doc, hit, search_term): hit 
                    for hit in hits
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_doc):
                    doc = future_to_doc[future]
                    try:
                        # 获取处理结果
                        doc_results = future.result()
                        
                        # 更新计数器和结果列表（线程安全）
                        with processed_count_lock:
                            processed_count += 1
                            if processed_count % 100 == 0:
                                logger.info(f"已处理 {processed_count} 个文档，找到 {len(all_results)} 条相关作者记录")
                        
                        # 添加结果到全局列表
                        if doc_results:
                            with results_lock:
                                all_results.extend(doc_results)
                                
                    except Exception as e:
                        logger.error(f"处理文档 {doc.get('_id')} 的任务失败: {str(e)}")
                        continue
            
            # 获取下一批数据
            try:
                result = es_client.client.scroll(scroll_id=scroll_id, scroll='2m')
                scroll_id = result['_scroll_id']
                result_body = result.get('body', result) if 'body' in result else result
                hits = result_body.get("hits", {}).get("hits", [])
            except Exception as e:
                logger.error(f"获取下一批数据时出错: {str(e)}")
                break
        
        # 清理scroll上下文
        try:
            es_client.client.clear_scroll(scroll_id=scroll_id)
        except Exception as e:
            logger.warning(f"清理scroll上下文时出错: {str(e)}")
        
        logger.info(f"处理完成！共处理了 {processed_count} 个文档，找到 {len(all_results)} 条相关作者记录")
        
        # 保存到Excel文件
        if save_to_excel and all_results:
            # 创建DataFrame
            df = pd.DataFrame(all_results)
            
            filename = f"{search_term}_papers_authors.xlsx"
            
            # 确保output目录存在
            output_dir = "output/power/"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            filepath = os.path.join(output_dir, filename)
            
            # 保存到Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"结果已保存到: {filepath}")
            logger.info(f"Excel文件包含 {len(all_results)} 条相关作者记录")
        
        elif save_to_excel and not all_results:
            logger.info("没有找到相关作者，未生成Excel文件")
            
    except Exception as e:
        logger.error(f"搜索过程中发生错误: {str(e)}")
        # 尝试清理scroll上下文
        try:
            if 'scroll_id' in locals():
                es_client.client.clear_scroll(scroll_id=scroll_id)
        except:
            pass
        return []
    
    return all_results


def process_companies_from_excel(excel_path: str, batch_size: int = 2000, max_workers: int = 20):
    """
    从Excel文件中读取机构名称并处理每个机构
    
    Args:
        excel_path: Excel文件路径
        batch_size: 每批次处理的文档数量
        max_workers: 最大线程数
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        # 获取机构名称列
        companies = df['机构名称'].dropna().unique()
        total_companies = len(companies)
        
        logger.info(f"从Excel中读取到 {total_companies} 个机构")
        
        # 处理每个机构
        for idx, company in enumerate(companies, 1):
            logger.info(f"\n处理第 {idx}/{total_companies} 个机构: {company}")
            
            try:
                # 搜索并处理当前机构
                results = search_company_papers(
                    search_term=company,
                    batch_size=batch_size,
                    save_to_excel=True,
                    max_workers=max_workers
                )
                
                logger.info(f"机构 {company} 处理完成，找到 {len(results)} 条记录")
                
            except Exception as e:
                logger.error(f"处理机构 {company} 时出错: {str(e)}")
                continue
            
            # 每处理完一个机构暂停1秒，避免请求过于频繁
            time.sleep(1)
        
        logger.info("\n所有机构处理完成！")
        
    except Exception as e:
        logger.error(f"处理Excel文件时出错: {str(e)}")


if __name__ == "__main__":
    # 设置处理参数
    EXCEL_PATH = "data/论文提取的国内企业.xlsx"  # Excel文件路径
    BATCH_SIZE = 2000  # 每批次处理的文档数量
    MAX_WORKERS = 20  # 最大线程数
    
    # 开始处理
    process_companies_from_excel(
        excel_path=EXCEL_PATH,
        batch_size=BATCH_SIZE,
        max_workers=MAX_WORKERS
    )
