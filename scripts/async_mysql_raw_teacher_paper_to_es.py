import os
import configparser
import asyncio
import argparse
from sqlalchemy import create_engine, text
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from tqdm import tqdm
import aiofiles
from contextlib import asynccontextmanager

# config = configparser.ConfigParser()
# config.read('/root/gcy/db_config.ini')

db_config = {
    'user': 'zwx',
    'password': '006af022-f15c-442c-8c56-e71a45d4531e',
    'host': '172.22.121.11',
    'port': 43200,
    'database': 'personnel-matching-new'
}

es_config = {
    'host': '172.22.121.11',
    'port': 39200,
    'user': 'elastic', 
    'password': '6fYUYglM6Cj6rHgQkt6D'
}


db_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset=utf8mb4"
engine = create_engine(db_url, pool_recycle=3600) 

@asynccontextmanager
async def get_es_client():
    es = AsyncElasticsearch(
        hosts=[{"scheme": "http", "host": es_config['host'], "port": es_config['port']}],
        basic_auth=(es_config['user'], es_config['password']),  
        request_timeout=30
    )
    try:
        yield es
    finally:
        await es.close()
        print("已关闭AsyncElasticsearch客户端")

# --------------------------
# 3. 常量配置
# --------------------------
INDEX_NAME = "raw_teacher_paper_88"  
BATCH_SIZE = 5000  # 增加批量大小以提高性能
SUB_BATCH_SIZE = 1000  # 增加子批量大小
ES_BULK_SIZE = 5000  # 增加ES批量大小
TABLE_NAME = "raw_teacher_paper" 
CHECKPOINT_FILE = "es_import_paper_checkpoint.txt"  
MAX_CONCURRENT_TASKS = 10  # 增加并发任务数


# --------------------------
# 4. 核心函数
# --------------------------
async def create_es_index(es):
    """异步创建ES索引"""
    if await es.indices.exists(index=INDEX_NAME):
        print(f"索引 {INDEX_NAME} 已存在，跳过创建")
        return

    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "long"}, 
                "title": {
                    "type": "keyword",
                    "fields": {
                        "lowercase": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer"
                        }
                    }
                },
                "paper_source": {
                    "type": "keyword"
                },
                "data_source_id": {
                    "type": "keyword"
                },
                "doi": {
                    "type": "keyword",
                    "eager_global_ordinals": "true"
                }, 
                "author_list": {
                    "type": "text", 
                    "analyzer": "semicolon_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                            "eager_global_ordinals": "true"
                        }
                    }
                },
                "affiliations": {
                    "type": "text", 
                    "analyzer": "semicolon_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                            "eager_global_ordinals": "true"
                        }
                    }
                },
                "email_addresses": {
                    "type": "text", 
                    "analyzer": "semicolon_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                            "eager_global_ordinals": "true"
                        }
                    }
                },
                "addresses": {
                    "type": "text",
                    "analyzer": "keyword",  
                    "index": False 
                },
                "research_area": {"type": "keyword", "index": False, "doc_values": False},
                "keywords": {"type": "keyword", "index": False, "doc_values": False},
                "keywords_plus": {"type": "keyword", "index": False, "doc_values": False},
                "reprint_addresses": {"type": "keyword", "index": False, "doc_values": False},
                "publication_date": {
                    "type": "keyword"
                }
            }
        },
        "settings": {
            "number_of_shards": 10,
            "number_of_replicas": 1,
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "filter": ["lowercase"]
                    }
                },
                "analyzer": {
                    "semicolon_analyzer": {
                        "type": "custom",
                        "tokenizer": "semicolon_tokenizer",
                        "filter": ["lowercase"]
                    }
                },
                "tokenizer": {
                    "semicolon_tokenizer": {"type": "pattern", "pattern": "\\s*;\\s*"}
                }
            }
        }
    }

    await es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"索引 {INDEX_NAME} 创建成功")    


def get_total_records():
    """获取总记录数（同步操作）"""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
        return result.scalar()


def generate_actions(last_id, batch_size):
    """从数据库读取一批数据（同步操作），生成ES批量导入的动作"""
    query = text(f"""
        SELECT id, author_list, paper_source, addresses, affiliations, title, research_area, 
               keywords, keywords_plus, email_addresses, reprint_addresses, publication_date, data_source_id, doi
        FROM {TABLE_NAME} 
        WHERE id > :last_id 
        ORDER BY id 
        LIMIT :batch_size
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"last_id": last_id, "batch_size": batch_size})
        rows = result.fetchall()
        if not rows:
            return [], None

        current_max_id = rows[-1][0]

        actions = []
        for row in rows:
            row_dict = dict(row._mapping)
            doc_id = row_dict['id']
            actions.append({
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": {
                    "id": int(doc_id),
                    "title": row_dict.get("title", ""),
                    "author_list": row_dict.get("author_list", ""),
                    "paper_source": row_dict.get("paper_source", ""),
                    "affiliations": row_dict.get("affiliations", ""),
                    "email_addresses": row_dict.get("email_addresses", ""),
                    "addresses": row_dict.get("addresses", ""),
                    "research_area": row_dict.get("research_area", ""),
                    "keywords": row_dict.get("keywords", ""),
                    "keywords_plus": row_dict.get("keywords_plus", ""),
                    "reprint_addresses": row_dict.get("reprint_addresses", ""),
                    "publication_date": row_dict.get("publication_date", ""),
                    "data_source_id": row_dict.get("data_source_id", ""),
                    "doi": row_dict.get("doi", "")
                }
            })

        return actions, current_max_id


async def process_sub_batch(es, actions, semaphore):
    """处理子批次数据"""
    async with semaphore:
        success, failed = await async_bulk(
            es,
            actions,
            chunk_size=ES_BULK_SIZE,
            max_retries=3,
            raise_on_error=False,
            stats_only=False
        )
        
        failed_details = []
        if failed:
            for item in failed:
                if "index" in item and "error" in item["index"]:
                    doc_id = item["index"]["_id"]
                    error_type = item["index"]["error"]["type"]
                    error_reason = item["index"]["error"]["reason"]
                    failed_details.append(f"ID: {doc_id}，类型: {error_type}，原因: {error_reason}")
        
        return len(actions), failed_details


async def save_checkpoint(last_id):
    """异步保存断点"""
    async with aiofiles.open(CHECKPOINT_FILE, "w") as f:
        await f.write(str(last_id))
    print(f"已保存断点：{last_id}")


async def load_checkpoint():
    """异步读取断点"""
    if not os.path.exists(CHECKPOINT_FILE):
        return 0

    async with aiofiles.open(CHECKPOINT_FILE, "r") as f:
        content = await f.read()
        try:
            return int(content.strip())
        except ValueError:
            print("断点文件格式错误，将从头开始")
            return 0


async def import_data(limit=None):
    """从数据库批量导入ES的主函数
    
    Args:
        limit (int, optional): 限制导入的记录数量。默认为None，表示导入全部数据。
    """
    async with get_es_client() as es:
        await create_es_index(es)
        total_available = get_total_records()
        total = min(total_available, limit) if limit else total_available
        print(f"数据库总记录数：{total_available}")
        print(f"计划导入记录数：{total}，开始导入...")


        last_id = await load_checkpoint()
        if last_id > 0:
            print(f"检测到断点，将从 id={last_id} 开始导入")
        else:
            print("未检测到断点，将从头开始导入")


        await es.indices.put_settings(
            index=INDEX_NAME,
            body={"index": {"refresh_interval": "-1", "number_of_replicas": 0}}
        )

        processed = 0 
        if last_id > 0:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE id <= :last_id"), {"last_id": last_id})
                processed = result.scalar() or 0


        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

        try:
            # 主进度条
            with tqdm(
                total=total,
                initial=processed,
                desc="数据导入进度",
                unit="条",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
            ) as pbar:
                while True:
                    actions, current_max_id = generate_actions(last_id, BATCH_SIZE)
                    if not actions:
                        break 


                    sub_batches = [
                        actions[i:i+SUB_BATCH_SIZE] 
                        for i in range(0, len(actions), SUB_BATCH_SIZE)
                    ]
                    print(f"当前主批次包含 {len(sub_batches)} 个子批次，开始并行处理...")


                    tasks = []
                    for sub_batch in sub_batches:
                        task = asyncio.create_task(process_sub_batch(es, sub_batch, semaphore))
                        tasks.append(task)

                    results = await asyncio.gather(*tasks)

                    batch_processed = 0
                    all_failed_details = []
                    for processed_count, failed_details in results:
                        batch_processed += processed_count
                        all_failed_details.extend(failed_details)

                    if all_failed_details:
                        print(f"⚠️ 本批次导入失败 {len(all_failed_details)} 条")
                        async with aiofiles.open("failed_ids_with_reason.txt", "a", encoding="utf-8") as f:
                            await f.write("\n".join(all_failed_details) + "\n")
                    else:
                        print("✅ 本批次所有数据导入成功")

                    # 更新进度
                    processed += batch_processed
                    last_id = current_max_id
                    await save_checkpoint(last_id)
                    pbar.update(batch_processed)
                    await asyncio.sleep(0.5)
                    
                    # 如果设置了限制并且已达到限制，则退出
                    if limit and processed >= limit:
                        print(f"\n已达到指定的导入数量限制({limit})，停止导入")
                        break

            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
                print("导入完成，已删除断点文件")

        finally:
            await es.indices.put_settings(
                index=INDEX_NAME,
                body={"index": {"refresh_interval": "1s", "number_of_replicas": 1}}
            )
            print("已恢复ES索引设置")

    print(f"导入完成，累计处理 {processed} 条记录")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从MySQL导入数据到Elasticsearch')
    parser.add_argument('--limit', type=int, help='限制导入的记录数量，默认导入全部数据')
    args = parser.parse_args()
    
    asyncio.run(import_data(limit=args.limit))


# 2025/07/11 导入完成，累计处理 48366609 条记录
# 导入完成，累计处理 48366609 条记录