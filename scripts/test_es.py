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


def search_one_phase():
    """
    一次查询 - 直接获取完整文档
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
    
    print("【一次查询】直接获取完整文档")
    
    start_time = time.time()
    results = es_client.search(index=index, query=query, size=10000)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    total_hits = results.get("hits", {}).get("total", {}).get("value", 0)
    returned_hits = len(results.get("hits", {}).get("hits", []))
    
    print(f"耗时: {elapsed_time:.3f}秒 ({elapsed_time*1000:.1f}ms)")
    print(f"结果: {total_hits}条，返回: {returned_hits}条")
    
    return results, elapsed_time


def search_two_phase():
    """
    二次查询 - 先查ID，再查详情
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
    
    print("\n【二次查询】先查ID，再查详情")
    
    total_start_time = time.time()
    
    # 第一步：只查询ID
    print("第一步: 查询ID...")
    phase1_start = time.time()
    
    body = {
        "query": query,
        "size": 10000,
        "_source": False,
        "fields": ["_id"]
    }
    
    id_results = es_client.client.search(index=index, body=body)
    phase1_end = time.time()
    phase1_time = phase1_end - phase1_start
    
    hits = id_results.get("hits", {}).get("hits", [])
    doc_ids = [hit["_id"] for hit in hits]
    
    # 生成SQL文件
    generate_sql_file(doc_ids)

    print(f"  耗时: {phase1_time:.3f}秒，获取ID: {len(doc_ids)}个")
    
    # 第二步：根据ID批量获取文档
    print("第二步: 批量获取文档...")
    phase2_start = time.time()
    
    docs_body = {"ids": doc_ids}
    full_results = es_client.client.mget(index=index, body=docs_body)
    
    phase2_end = time.time()
    phase2_time = phase2_end - phase2_start
    total_time = phase2_end - total_start_time
    
    docs = full_results.get("docs", [])
    found_docs = [doc for doc in docs if doc.get("found", False)]
    
    print(f"  耗时: {phase2_time:.3f}秒，获取文档: {len(found_docs)}个")
    print(f"总耗时: {total_time:.3f}秒 ({total_time*1000:.1f}ms)")
    
    # 构造返回格式
    results = {
        "hits": {
            "total": {"value": len(found_docs)},
            "hits": [{"_id": doc["_id"], "_source": doc["_source"]} for doc in found_docs]
        }
    }
    
    return results, total_time


def performance_test():
    """
    性能对比测试
    """
    print("=" * 60)
    print("Elasticsearch 查询性能对比")
    print("=" * 60)
    
    # 测试一次查询
    # one_results, one_time = search_one_phase()
    
    # 测试二次查询
    two_results, two_time = search_two_phase()
    
    # # 对比结果
    # print("\n" + "=" * 60)
    # print("性能对比结果")
    # print("=" * 60)
    # print(f"一次查询耗时: {one_time:.3f}秒 ({one_time*1000:.1f}ms)")
    # print(f"二次查询耗时: {two_time:.3f}秒 ({two_time*1000:.1f}ms)")
    
    # if one_time < two_time:
    #     diff = two_time - one_time
    #     percentage = (diff / one_time) * 100
    #     print(f"一次查询更快: 快{diff:.3f}秒 ({percentage:.1f}%)")
    # else:
    #     diff = one_time - two_time
    #     percentage = (diff / two_time) * 100
    #     print(f"二次查询更快: 快{diff:.3f}秒 ({percentage:.1f}%)")
    
    # # 验证结果数量
    # one_count = len(one_results.get("hits", {}).get("hits", []))
    # two_count = len(two_results.get("hits", {}).get("hits", []))
    # print(f"\n结果验证:")
    # print(f"一次查询: {one_count}条")
    # print(f"二次查询: {two_count}条")
    # print(f"结果一致: {'✓' if one_count == two_count else '✗'}")


if __name__ == "__main__":
    performance_test()