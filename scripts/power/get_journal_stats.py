from elasticsearch import Elasticsearch
import pandas as pd
from talent_platform.config import config
from talent_platform.es.client import get_es_client
from talent_platform.logger import logger

def get_journal_stats():
    """获取所有期刊的统计信息"""
    client = get_es_client()
    
    # 聚合查询
    composite_query = {
        "size": 0,
        "aggs": {
            "journals": {
                "composite": {
                    "size": 1000,  # 每页大小
                    "sources": [
                        {
                            "journal": {
                                "terms": {
                                    "field": "journal"
                                }
                            }
                        }
                    ]
                }
            }
        }
    }

    try:
        all_buckets = []
        has_more = True
        after_key = None
        total_journals = 0

        while has_more:
            # 添加after_key到查询中
            if after_key:
                composite_query["aggs"]["journals"]["composite"]["after"] = after_key

            # 执行查询
            response = client.search(
                index="raw_teacher_cn_paper",
                body=composite_query
            )
            
            # 获取当前批次的buckets
            buckets = response.body["aggregations"]["journals"]["buckets"]
            
            # 如果没有更多结果，退出循环
            if not buckets:
                has_more = False
                continue
                
            # 保存结果
            all_buckets.extend(buckets)
            total_journals += len(buckets)
            
            # 获取after_key用于下一次查询
            after_key = response.body["aggregations"]["journals"].get("after_key")
            has_more = after_key is not None
            
            logger.info(f"已获取 {total_journals} 个期刊的统计信息")
        
        # 转换为DataFrame
        data = [
            {
                "期刊名称": bucket["key"]["journal"],
                "论文数量": bucket["doc_count"]
            }
            for bucket in all_buckets
        ]
        
        df = pd.DataFrame(data)
        
        # 按论文数量降序排序
        df = df.sort_values(by="论文数量", ascending=False)
        
        # 保存为Excel
        output_file = "output/journal_statistics.xlsx"
        df.to_excel(output_file, index=False)
        logger.info(f"统计结果已保存到: {output_file}")
        logger.info(f"共统计了 {len(df)} 个期刊")
        
    except Exception as e:
        logger.error(f"获取期刊统计信息失败: {str(e)}")
        raise

if __name__ == "__main__":
    get_journal_stats()
