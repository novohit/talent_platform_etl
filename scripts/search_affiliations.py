from talent_platform.es.client import get_es_client
from collections import Counter
import pandas as pd
from datetime import datetime
import logging
import sys
import json
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

def search_all_affiliations():
    # 记录开始时间
    start_time = datetime.now()
    logging.info(f"开始时间: {start_time}")
    
    # 获取ES客户端
    es = get_es_client()
    logging.info("开始连接Elasticsearch...")
    
    # 初始化计数器
    affiliation_counter = Counter()
    
    # 初始化composite聚合查询
    batch_size = 5000  # 每批次获取的桶数量
    
    body = {
        "size": 0,
        "aggs": {
            "all_affiliations": {
                "composite": {
                    "size": batch_size,
                    "sources": [
                        {"affiliation": {"terms": {"field": "affiliations.keyword"}}}
                    ]
                }
            }
        }
    }
    
    logging.info("开始查询papers_20250808索引...")
    
    total_buckets = 0
    batch_count = 0
    has_more = True
    
    # 创建进度条（初始设置为一个较大的值，后续会更新）
    progress_bar = tqdm(desc="处理分组", unit="bucket")
    
    while has_more:
        batch_count += 1
        logging.info(f"正在处理第 {batch_count} 批聚合数据...")
        
        # 执行查询
        result = es.search(index="papers_20250808", body=body)
        
        # 获取当前批次的桶
        buckets = result["aggregations"]["all_affiliations"]["buckets"]
        current_batch_size = len(buckets)
        
        # 处理当前批次的结果
        for bucket in buckets:
            affiliation = bucket["key"]["affiliation"]
            count = bucket["doc_count"]
            if affiliation:  # 确保affiliation不为空
                affiliation_counter[affiliation] = count
        
        # 更新进度
        total_buckets += current_batch_size
        progress_bar.total = total_buckets + batch_size  # 预估还有一批
        progress_bar.update(current_batch_size)
        
        # 检查是否还有更多结果
        if "after_key" in result["aggregations"]["all_affiliations"]:
            # 更新after_key用于下一次查询
            body["aggs"]["all_affiliations"]["composite"]["after"] = result["aggregations"]["all_affiliations"]["after_key"]
            logging.info(f"已处理 {total_buckets} 个分组")
        else:
            has_more = False
            progress_bar.total = total_buckets  # 设置最终的总数
            progress_bar.refresh()
    
    # 关闭进度条
    progress_bar.close()
    
    logging.info(f"聚合查询完成，共发现 {total_buckets} 个不同的机构")
    
    # 将结果按计数排序并转换为列表
    sorted_affiliations = sorted(
        affiliation_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # 将结果保存到文件
    result_dict = {
        "total_unique_affiliations": len(sorted_affiliations),
        "affiliations": [
            {"affiliation": aff, "count": count}
            for aff, count in sorted_affiliations
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(sorted_affiliations, columns=['机构名称', '出现次数'])
    
    # 添加排名列
    df.insert(0, '排名', range(1, len(df) + 1))
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_file = f"output/affiliations_analysis_{timestamp}.xlsx"
    
    # 保存为Excel文件
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='机构统计')
        
        # 获取工作表对象
        worksheet = writer.sheets['机构统计']
        
        # 调整列宽
        worksheet.column_dimensions['A'].width = 8  # 排名
        worksheet.column_dimensions['B'].width = 50  # 机构名称
        worksheet.column_dimensions['C'].width = 12  # 出现次数
    
    # 同时保存JSON文件以备后用
    json_file = f"output/affiliations_analysis_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    logging.info(f"共找到 {len(sorted_affiliations)} 个不同的机构")
    logging.info(f"结果已保存到Excel文件: {excel_file}")
    logging.info(f"JSON格式结果保存到: {json_file}")
    logging.info("\n前10个最常见的机构:")
    for aff, count in sorted_affiliations[:10]:
        logging.info(f"{aff}: {count}次引用")
    
    # 输出处理时间
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"\n总处理时间: {duration}")

if __name__ == "__main__":
    search_all_affiliations()
