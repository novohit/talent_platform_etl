import os
import asyncio
import argparse
from sqlalchemy import create_engine, text
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from tqdm import tqdm
import aiofiles
from contextlib import asynccontextmanager

# Database configuration
db_config = {
    'user': 'zwx',
    'password': '006af022-f15c-442c-8c56-e71a45d4531e',
    'host': '172.22.121.11',
    'port': 43200,
    'database': 'personnel-matching-new'
}

# Elasticsearch configuration
es_config = {
    'host': '172.22.121.11',
    'port': 39200,
    'user': 'elastic', 
    'password': '6fYUYglM6Cj6rHgQkt6D'
}

# Create database URL and engine
db_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset=utf8mb4"
engine = create_engine(db_url, pool_recycle=3600)

@asynccontextmanager
async def get_es_client():
    """Get Elasticsearch client with context management"""
    es = AsyncElasticsearch(
        hosts=[{"scheme": "http", "host": es_config['host'], "port": es_config['port']}],
        basic_auth=(es_config['user'], es_config['password']),  
        request_timeout=30
    )
    try:
        yield es
    finally:
        await es.close()
        print("Elasticsearch client closed")

# Constants
INDEX_NAME = "raw_google_european_patent"
BATCH_SIZE = 10000  # 增加批量大小
SUB_BATCH_SIZE = 2000  # 增加子批量大小
ES_BULK_SIZE = 10000  # 增加ES批量大小
TABLE_NAME = "raw_google_european_patent"  # Update this to match your actual table name
CHECKPOINT_FILE = "es_import_patent_checkpoint.txt"
MAX_CONCURRENT_TASKS = 20  # 增加并发数

async def create_es_index(es):
    """Create Elasticsearch index with mapping"""
    if await es.indices.exists(index=INDEX_NAME):
        print(f"Index {INDEX_NAME} already exists, skipping creation")
        return

    mapping = {
        "mappings": {
            "properties": {
                "patent_id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer"
                        }
                    }
                },
                "abstract": {
                    "type": "text"
                },
                "inventor": {
                    "type": "text",
                    "analyzer": "multi_separator_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer"
                        }
                    }
                },
                "application_number": {"type": "keyword"},
                "applicant": {
                    "type": "text",
                    "analyzer": "multi_separator_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer"
                        }
                    }
                },
                "data_source": {"type": "keyword"},
                "is_valid": {"type": "boolean"}
            }
        },
        "settings": {
            "number_of_shards": 10,  # 增加分片数
            "number_of_replicas": 0,  # 导入时不需要副本
            "refresh_interval": "30s",  # 降低刷新频率
            "translog": {
                "durability": "async",  # 异步事务日志
                "sync_interval": "30s"
            },
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "filter": ["lowercase"]
                    }
                },
                "analyzer": {
                    "multi_separator_analyzer": {
                        "type": "custom",
                        "tokenizer": "multi_separator_tokenizer",
                        "filter": ["lowercase"]
                    }
                },
                "tokenizer": {
                    "multi_separator_tokenizer": {
                        "type": "pattern",
                        "pattern": "\\s*[,;]\\s*"
                    }
                }
            }
        }
    }

    await es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Index {INDEX_NAME} created successfully")

def get_total_records():
    """Get total number of records in the database"""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
        return result.scalar()

def generate_actions(last_id, batch_size):
    """Generate actions for Elasticsearch bulk import"""
    query = text(f"""
        SELECT patent_id, title, abstract, inventor, application_number, 
               applicant, data_source, is_valid
        FROM {TABLE_NAME}
        WHERE patent_id > :last_id
        ORDER BY patent_id
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
            doc_id = row_dict['patent_id']
            actions.append({
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": {
                    "patent_id": doc_id,
                    "title": row_dict.get("title", ""),
                    "abstract": row_dict.get("abstract", ""),
                    "inventor": row_dict.get("inventor", ""),
                    "application_number": row_dict.get("application_number", ""),
                    "applicant": row_dict.get("applicant", ""),
                    "data_source": row_dict.get("data_source", ""),
                    "is_valid": bool(row_dict.get("is_valid", True))
                }
            })

        return actions, current_max_id

async def process_sub_batch(es, actions, semaphore):
    """Process a sub-batch of documents"""
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
                    failed_details.append(f"ID: {doc_id}, Type: {error_type}, Reason: {error_reason}")
        
        return len(actions), failed_details

async def save_checkpoint(last_id):
    """Save checkpoint to file"""
    async with aiofiles.open(CHECKPOINT_FILE, "w") as f:
        await f.write(str(last_id))
    print(f"Checkpoint saved: {last_id}")

async def load_checkpoint():
    """Load checkpoint from file"""
    if not os.path.exists(CHECKPOINT_FILE):
        return 0

    async with aiofiles.open(CHECKPOINT_FILE, "r") as f:
        content = await f.read()
        try:
            return int(content.strip())
        except ValueError:
            print("Invalid checkpoint file format, starting from beginning")
            return 0

async def import_data(limit=None):
    """Main function to import data from MySQL to Elasticsearch"""
    async with get_es_client() as es:
        await create_es_index(es)
        total_available = get_total_records()
        total = min(total_available, limit) if limit else total_available
        print(f"Total records in database: {total_available}")
        print(f"Planning to import: {total} records")

        last_id = await load_checkpoint()
        if last_id > 0:
            print(f"Checkpoint detected, starting from id={last_id}")
        else:
            print("No checkpoint found, starting from beginning")

        # Optimize ES index settings for bulk import
        await es.indices.put_settings(
            index=INDEX_NAME,
            body={"index": {"refresh_interval": "-1", "number_of_replicas": 0}}
        )

        processed = 0
        if last_id > 0:
            with engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE patent_id <= :last_id"),
                    {"last_id": last_id}
                )
                processed = result.scalar() or 0

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

        try:
            with tqdm(
                total=total,
                initial=processed,
                desc="Import progress",
                unit="records",
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
                    print(f"Current batch contains {len(sub_batches)} sub-batches")

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
                        print(f"⚠️ {len(all_failed_details)} records failed in this batch")
                        async with aiofiles.open("failed_patent_ids.txt", "a", encoding="utf-8") as f:
                            await f.write("\n".join(all_failed_details) + "\n")
                    else:
                        print("✅ All records in batch imported successfully")

                    processed += batch_processed
                    last_id = current_max_id
                    await save_checkpoint(last_id)
                    pbar.update(batch_processed)
                    await asyncio.sleep(0.5)

                    if limit and processed >= limit:
                        print(f"\nReached import limit ({limit}), stopping")
                        break

            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
                print("Import complete, checkpoint file removed")

        finally:
            # Restore ES index settings
            await es.indices.put_settings(
                index=INDEX_NAME,
                body={"index": {"refresh_interval": "1s", "number_of_replicas": 1}}
            )
            print("ES index settings restored")

    print(f"Import complete, processed {processed} records")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import patent data from MySQL to Elasticsearch')
    parser.add_argument('--limit', type=int, help='Limit the number of records to import (default: all)')
    args = parser.parse_args()
    
    asyncio.run(import_data(limit=args.limit))
