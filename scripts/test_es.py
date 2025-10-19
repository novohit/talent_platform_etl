from talent_platform.es.client import es_client
import time
import os


def generate_sql_file(doc_ids):
    """
    生成包含 IN 子句的 SQL 文件
    """
    if not doc_ids:
        print("没有找到文档ID，跳过SQL文件生成")
        return
    
    # 创建输出目录
    output_dir = "/Users/novo/code/python/talent_platform_etl/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成SQL文件路径
    sql_file_path = os.path.join(output_dir, "doc_ids_query.sql")
    
    # 格式化doc_ids为SQL IN子句
    # 假设这些ID是字符串类型，需要加引号
    formatted_ids = [f"'{doc_id}'" for doc_id in doc_ids]
    ids_str = ",\n    ".join(formatted_ids)
    
    # 生成SQL查询语句
    sql_content = f"""-- 基于Elasticsearch查询结果生成的SQL IN子句
-- 总共 {len(doc_ids)} 个文档ID

SELECT * 
FROM papers 
WHERE id IN (
    {ids_str}
);

-- 或者用于更新操作
-- UPDATE papers 
-- SET some_field = 'some_value'
-- WHERE id IN (
--     {ids_str}
-- );

-- 或者用于删除操作
-- DELETE FROM papers 
-- WHERE id IN (
--     {ids_str}
-- );
"""
    
    # 写入文件
    with open(sql_file_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"SQL文件已生成: {sql_file_path}")
    print(f"包含 {len(doc_ids)} 个文档ID")


def search_scroll():
    """
    滚动查询 - 分批次获取所有文档
    """
    index = "papers_20250808"
    
    author_variations = [
        "zhang, luyun", "lei li", "lilei", "li, l", "li, l.", 
        "lei, li", "l, lei", "li lei", "lei l.", "li l", 
        "li l.", "li, lei", "l li", "l., li", "lei, l", 
        "l lei", "lei l", "l. li", "lei, l.", "l., lei", 
        "l. lei", "l, li"
    ]
    
    query = {
        "bool": {
            "must": [
                {
                    "terms": {
                        "author_list.keyword": author_variations
                    }
                }
            ]
        }
    }
    
    print("【滚动查询】分批次获取所有文档")
    
    start_time = time.time()
    
    # 初始化滚动查询
    scroll_size = 1000  # 每批次获取的文档数量
    scroll_timeout = "2m"  # 滚动上下文保持时间
    
    # 第一次查询，建立滚动上下文
    body = {"query": query, "size": scroll_size}
    results = es_client.client.search(
        index=index, 
        body=body,
        scroll=scroll_timeout
    )
    
    # 获取响应体（Elasticsearch 8.x 返回的是对象，需要获取 body 属性）
    if hasattr(results, 'body'):
        results = results.body
    
    scroll_id = results.get("_scroll_id")
    all_hits = results.get("hits", {}).get("hits", [])
    total_hits = results.get("hits", {}).get("total", {}).get("value", 0)
    
    print(f"总共需要处理: {total_hits} 条记录")
    print(f"每批次处理: {scroll_size} 条记录")
    
    batch_count = 1
    print(f"批次 {batch_count}: 获取到 {len(all_hits)} 条记录")
    
    # 继续滚动获取剩余数据
    while len(results.get("hits", {}).get("hits", [])) > 0:
        try:
            # 使用滚动ID获取下一批数据
            results = es_client.client.scroll(scroll_id=scroll_id, scroll=scroll_timeout)
            
            # 获取响应体（Elasticsearch 8.x 返回的是对象，需要获取 body 属性）
            if hasattr(results, 'body'):
                results = results.body
                
            current_hits = results.get("hits", {}).get("hits", [])
            
            if not current_hits:
                break
                
            all_hits.extend(current_hits)
            batch_count += 1
            print(f"批次 {batch_count}: 获取到 {len(current_hits)} 条记录，累计: {len(all_hits)} 条")
            
        except Exception as e:
            print(f"滚动查询出错: {e}")
            break
    
    # 清理滚动上下文
    try:
        if scroll_id:
            es_client.client.clear_scroll(scroll_id=scroll_id)
            print("滚动上下文已清理")
    except Exception as e:
        print(f"清理滚动上下文失败: {e}")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"耗时: {elapsed_time:.3f}秒 ({elapsed_time*1000:.1f}ms)")
    print(f"总批次数: {batch_count}")
    print(f"预期结果: {total_hits}条，实际获取: {len(all_hits)}条")
    
    # 构造返回结果，保持与原函数相同的格式
    final_results = {
        "hits": {
            "total": {"value": total_hits},
            "hits": all_hits
        }
    }
    
    return final_results, elapsed_time



def search_papers_by_author_variations():
    """
    执行指定的论文作者查询
    查询条件：按照多种作者名称变体进行搜索
    """
    index = "raw_teacher_paper_88"
    
    
    # 构建查询体
    query_body = {
  "size": 10000,
  "query": {
      
    "bool": {"must": [{"terms": {"author_list": ["r.c yi", "yi, r -c.", "ran c.yi", "chen yi-ran", "chen, y. r.", "yi -r. chen", "r.-chen yi", "yiranc", "y-r, chen", "y. -rchen", "y.ran-chen", "y-ranchen", "y chen", "yi ran chen", "yi, r-chen", "y. r. chen", "yir. chen", "y -r chen", "r. c., yi", "yi r c.", "c.yi-ran", "y. r., chen", "chen yi -ran", "yi, r. -c", "r cyi", "chen yi-r.", "y. r, chen", "yir. -c.", "yi r. c", "yi r -c", "chen y.-r", "yi ran, c.", "y.r. chen", "yi -ran, chen", "yi-ran chen", "cheny.-ran", "ran -cyi", "r. c.yi", "yi, r c.", "yi -rchen", "r-cyi", "chen yiran", "y, ranchen", "c yi-ran", "ranchen, yi", "r, yi", "yr., chen", "rc yi", "yi ran, c", "yi, r. c", "y-r., chen", "c. yi ran", "yi r.c.", "chen, yr.", "yranchen", "yir. -chen", "yi, r", "yi-r, chen", "yi ran -c", "yi r.-c", "c, yiran", "yir -c.", "r.-c. yi", "chen y. ran", "yi r-c", "yir-c", "r-c, yi", "y -ran, chen", "r -chen yi", "r c yi", "c., yiran", "y.ran chen", "r.-c., yi", "yiran c", "y ran-chen", "yi r -c.", "chen, yi-ran", "chen, yi-r.", "y.rchen", "y.ranchen", "yi r", "y-r. chen", "yir. -c", "yiran -c.", "r-chen, yi", "r.-c yi", "cheny -ran", "y r., chen", "chen, y. -ran", "cheny", "yi-r chen", "y. ranchen", "ran -chen yi", "yi rc", "chen, y.r.", "chen, yi r.", "r. c. yi", "y.-r. chen", "chen y.", "ran-cyi", "chen, y r", "cheny r", "chenyi r.", "chen, yi r", "chen y -ran", "y., ran chen", "ranchen y", "yi-ran, chen", "y., ran-chen", "yi -r., chen", "ran-c., yi", "cheny. -ran", "yi, ran c", "r chenyi", "chen, y", "cheny.", "r. -c yi", "y.r, chen", "yir-chen", "yi, r.c", "yi-ran c", "r. -chen yi", "yi -ranchen", "ran -c. yi", "yi, r.-chen", "cheny.r.", "r.-c, yi", "yi, ran chen", "c.yiran", "rcyi", "yi ran -c.", "chen y r.", "yi r-c.", "yir. c", "r.c.yi", "yi ran, chen", "ran-c, yi", "r. -c., yi", "ran -c, yi", "y.-r, chen", "ran-chenyi", "ranchen y.", "ran-c.yi", "y. r chen", "yi r -chen", "chen, y.-r.", "yi r-chen", "yran-chen", "ran cyi", "y ran chen", "yi-ranchen", "yiran -chen", "ran-cheny", "yi r.-chen", "ran chen y.", "yir-c.", "ran-chen y", "r-chenyi", "y.chen", "r. cyi", "y. chen", "chen y. -ran", "ran -chenyi", "yi r. chen", "yi rc.", "yi ranc.", "ran -c.yi", "chen, yi -r.", "chen yi -r.", "yi ran c", "r. yi", "r. chen, yi", "yi-ranc", "r -c. yi", "chen y -r.", "yir c", "r -c yi", "chen, y -ran", "chen y. -r.", "ran-chen, y", "y. ran chen", "yi, r.-c.", "y -r, chen", "yi r. c.", "chen y-r.", "chen y.r.", "cheny.-r", "chen, yr", "yir chen", "yi r.chen", "rc., yi", "yir c.", "y. -r. chen", "r. -c, yi", "y. -r chen", "r chen, yi", "y -ranchen", "chen, y.r", "yran chen", "r -chen, yi", "rancheny", "yi r c", "rc, yi", "c., yi-ran", "yi r chen", "r -chenyi", "ran c, yi", "r. c, yi", "yiran, c.", "yir.c.", "yi, r chen", "chen y ran", "c. yi-ran", "chen, y. -r.", "r c, yi", "ran cheny", "cheny. -r", "yir. c.", "yi-r., chen", "yi r. -c", "y r.chen", "chen, y.-ran", "chen, y.", "chen, y.-r", "cyi-ran", "yi, r -chen", "ran-c. yi", "yi, r -c", "yi, ran-chen", "yi-ran, c", "chen y-ran", "cheny r.", "y-r.chen", "yi -ran chen", "ran-chen y.", "r-chen yi", "yir.", "yi, r.-c", "yiran chen", "ran c yi", "chen yi -r", "chen, y. -r", "chen, yiran", "y. -ran, chen", "cheny. r.", "chenyi-r", "r. -c. yi", "c., yi ran", "chen, y r.", "yi, r.c.", "yi-ran c.", "yi, ranchen", "rc.yi", "y.-rchen", "chen, y -r.", "cyiran", "ran chen, yi", "yi, rc", "y -r.chen", "y. r.chen", "yi ran-chen", "yir.-chen", "y.-ran chen", "cheny -r", "chen yr", "r-c. yi", "yi, r. -chen", "yr. chen", "c, yi-ran", "ranchen, y", "y.-r., chen", "chen y. -r", "chen y", "yi, r-c", "yi-ran, c.", "chen, yi -ran", "y -rchen", "yir.-c", "r.c. yi", "yirc.", "yrchen", "y.-ranchen", "y, chen", "c.yi ran", "r.-c.yi", "ran chen, y.", "y. -r.chen", "chen yi-r", "r-c., yi", "r. c yi", "r-c.yi", "ran -chen, yi", "chenyi ran", "yiran-chen", "cheny-r.", "cheny-ran", "chenyi-ran", "r. -chenyi", "chen, y-ran", "y-rchen", "chen, yi -r", "yi r, chen", "chen, y-r", "y.-r chen", "y.r.chen", "c, yi ran", "ran-cheny.", "cyi ran", "chen y.-ran", "c yiran", "chen y r", "y.r., chen", "ran-chen yi", "yi, ran -chen", "y ranchen", "chen, yi-r", "ran chen yi", "ran-chen, y.", "y. -ran chen", "yi-r. chen", "yi, r. c.", "c. yiran", "chen y.r", "y. -r., chen", "yi, rc.", "r. -chen, yi", "yi rchen", "ran chenyi", "yiranc.", "r -c., yi", "chenyr", "yir -chen", "chen y-r", "chenyr.", "y, ran chen", "y.r chen", "r.cyi", "chen, yi ran", "yirc", "ran-c yi", "yiran-c", "y. ran, chen", "yi, ran-c.", "yi, ran -c", "y ran, chen", "yiranchen", "chenyi r", "yi ran c.", "yi, ran c.", "chen y. r", "ran chen, y", "y. rchen", "y rchen", "r chen yi", "chen yi r", "yir", "yr chen", "chen y. r.", "yi ranchen", "yiran-c.", "yi, r. -c.", "chen, y-r.", "yir.c", "y r chen", "chenyi -r.", "chenyi -ran", "cheny-r", "yi, ran -c.", "ran -c yi", "cheny -r.", "y -r. chen", "cheny.-r.", "rancheny.", "cheny ran", "cheny. r", "yi-rchen", "chen, y ran", "cheny. -r.", "ran -c., yi", "chen yi r.", "ychen", "cheny.r", "ran-chen, yi", "r -c, yi", "yi ran-c", "chen, y. r", "y., chen", "r. chen yi", "yiran, chen", "yiran c.", "y r, chen", "y.-ran, chen", "yi -r.chen", "yi r. -chen", "yi, r. chen", "y., ranchen", "yir.-c.", "rc. yi", "r.-chenyi", "yi -r, chen", "ran cheny.", "yi r.-c.", "chen y.-r.", "yiran -c", "y-ran chen", "r yi", "y-ran, chen", "chenyi-r.", "y -ran chen", "r c. yi", "yi ran -chen", "yi-r.chen", "c yi ran", "r., yi", "chen yr.", "chen, y -r", "yr, chen", "yi r.c", "r-c yi", "chen yi ran", "y. -ranchen", "r.yi", "r.-chen, yi", "r -cyi", "ranchen yi", "y-r chen", "ryi", "yi r.", "ran c., yi", "r. -c.yi", "yi, r-c.", "r.c., yi", "yi, r.", "y. ran-chen", "yir -c", "chenyiran", "chenyi -r", "yi ran-c.", "cheny. ran", "yi r. -c.", "yi-ranc.", "yiran, c", "r. -cyi", "ranchen, y.", "y, ran-chen", "y -r., chen", "yi, r c", "r. chenyi", "r c.yi", "r.-cyi", "chen y -r", "yi -r chen", "r c., yi", "ran chen y", "y.-r.chen", "yr.chen", "yi ranc", "r -c.yi", "yi, ran-c", "y. -r, chen", "r.c, yi", "ranchenyi", "yi r., chen", "ran c. yi", "y r. chen", "chen, y. ran"]}}, {"terms": {"affiliations": ["duke university"]}}]}
  }

}
    
    print("=" * 80)
    print("执行论文作者查询")
    print("=" * 80)
    print(f"索引: {index}")
    print(f"查询大小: {query_body['size']}")
    print()
    
    start_time = time.time()
    
    try:
        # 执行查询
        response = es_client.client.search(index=index, body=query_body)
        
        # 获取响应体（Elasticsearch 8.x 返回的是对象，需要获取 body 属性）
        if hasattr(response, 'body'):
            results = response.body
        else:
            results = response
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 解析结果
        hits = results.get("hits", {})
        total_hits = hits.get("total", {}).get("value", 0)
        documents = hits.get("hits", [])
        
        print(f"查询完成！")
        print(f"耗时: {elapsed_time:.3f}秒 ({elapsed_time*1000:.1f}ms)")
        print(f"找到文档数量: {total_hits}")
        print(f"返回文档数量: {len(documents)}")
        
        # 显示性能分析信息（如果启用了profile）
        if results.get("profile"):
            print("\n性能分析信息:")
            profile_info = results["profile"]["shards"][0]["searches"][0]
            query_time = profile_info.get("query", [{}])[0].get("time_in_nanos", 0) / 1_000_000
            print(f"查询阶段耗时: {query_time:.2f}ms")
        
        # 显示前几个文档的基本信息
        if documents:
            print(f"\n前 {min(5, len(documents))} 个文档信息:")
            for i, doc in enumerate(documents[:5]):
                source = doc.get("_source", {})
                doc_id = source.get("id") or doc.get("_id")
                title = source.get("title", "N/A")[:50] + "..." if len(source.get("title", "")) > 50 else source.get("title", "N/A")
                authors = source.get("author_list", [])
                
                print(f"  [{i+1}] ID: {doc_id}")
                print(f"      标题: {title}")
                print(f"      作者: {authors[:3]}{'...' if len(authors) > 3 else ''}")
                print()
        
        # 提取所有文档ID
        doc_ids = []
        for hit in documents:
            doc_id = hit.get("_source", {}).get("id") or hit.get("_id")
            if doc_id:
                doc_ids.append(doc_id)
        
        # 生成SQL文件
        if doc_ids:
            print(f"提取到 {len(doc_ids)} 个文档ID，正在生成SQL文件...")
            generate_sql_file(doc_ids)
        
        return results, elapsed_time
        
    except Exception as e:
        print(f"查询执行失败: {e}")
        raise


def performance_test():
    """
    性能对比测试
    """
    print("=" * 60)
    print("Elasticsearch 滚动查询测试")
    print("=" * 60)
    
    # 执行滚动查询
    results, elapsed_time = search_scroll()
    
    # 提取文档ID
    doc_ids = []
    for hit in results.get("hits", {}).get("hits", []):
        doc_id = hit.get("_source", {}).get("id") or hit.get("_id")
        if doc_id:
            doc_ids.append(doc_id)
    
    print(f"\n提取到 {len(doc_ids)} 个文档ID")
    
    # 生成SQL文件
    if doc_ids:
        generate_sql_file(doc_ids)


if __name__ == "__main__":
    import sys
    search_papers_by_author_variations()
    exit()
    if len(sys.argv) > 1 and sys.argv[1] == "author_search":
        # 执行作者变体查询
        search_papers_by_author_variations()
    else:
        # 默认执行性能测试
        performance_test()