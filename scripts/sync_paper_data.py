import json
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlmodel import select, Session, text
from talent_platform.db.database import get_session
from talent_platform.es.client import es_client
from talent_platform.logger import logger


def get_min_max_id(session: Session) -> tuple[int, int]:
    """获取数据表中最小和最大的ID"""
    min_id_query = text("SELECT MIN(id) as min_id FROM raw_teacher_paper")
    max_id_query = text("SELECT MAX(id) as max_id FROM raw_teacher_paper")
    
    min_id = session.exec(min_id_query).first()[0] or 0
    max_id = session.exec(max_id_query).first()[0] or 0
    
    return min_id, max_id

def sync_paper_data_by_range(session: Session, start_id: int, end_id: int) -> List[Dict[str, Any]]:
    """按ID范围获取论文数据"""
    statement = text("""
        SELECT 
            id,
            title,
            paper_source,
            data_source_id,
            doi,
            author_list,
            affiliations,
            email_addresses,
            addresses,
            research_area,
            keywords,
            keywords_plus,
            reprint_addresses,
            publication_date
        FROM raw_teacher_paper
        WHERE id >= :start_id AND id < :end_id
        ORDER BY id
    """)
    
    result = session.exec(statement, params={"start_id": start_id, "end_id": end_id})
    return list(result.mappings())

def sync_paper_data(batch_size: int = 10000) -> None:
    """使用ID分页同步论文数据"""
    checkpoint_file = "cache/paper_sync_checkpoint.json"
    
    # 如果存在检查点文件，从上次的位置继续
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            checkpoint = json.load(f)
            current_id = checkpoint["last_processed_id"]
            logger.info(f"Resuming from checkpoint, last processed ID: {current_id}")
    else:
        current_id = None

    with get_session() as session:
        min_id, max_id = get_min_max_id(session)
        
        if current_id is None:
            current_id = min_id
        
        total_records = max_id - min_id + 1
        logger.info(f"Total records to process: {total_records} (ID range: {min_id} to {max_id})")
        
        while current_id <= max_id:
            end_id = min(current_id + batch_size, max_id + 1)
            logger.info(f"Processing ID range: {current_id} to {end_id-1}")
            
            # 获取当前批次的数据
            batch_data = sync_paper_data_by_range(session, current_id, end_id)
            
            if batch_data:
                # 处理并索引数据
                process_batch("papers_20250808", batch_data)
                
                # 更新检查点
                with open(checkpoint_file, "w") as f:
                    json.dump({"last_processed_id": end_id - 1, "timestamp": datetime.now().isoformat()}, f)
            
            current_id = end_id
            
            # 记录进度
            progress = (current_id - min_id) / total_records * 100
            logger.info(f"Progress: {progress:.2f}% completed")


def create_paper_index(index: str):
    """Create or recreate the paper index with proper mappings"""
    es_client.delete_index(index)
    
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
                "paper_source": {"type": "keyword"},
                "data_source_id": {"type": "keyword"},
                "doi": {
                    "type": "keyword",
                    "eager_global_ordinals": "true"
                },
                "author_list": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                            "eager_global_ordinals": "true"
                        },
                        "exact": {
                            "type": "keyword",
                            "eager_global_ordinals": "true"
                        }
                    }
                },
                "affiliations": {
                    "type": "text", 
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer",
                            "eager_global_ordinals": "true"
                        },
                        "exact": {
                            "type": "keyword",
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
                "publication_date": {"type": "keyword"}
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
    
    es_client.create_index(index, mapping)


def process_semicolon_separated_string(input_str: str) -> List[str]:
    """将分号分隔的字符串转换为数组"""
    if not input_str:
        return []
    # 按分号分割并清理空白
    return [item.strip() for item in input_str.split(';') if item.strip()]

def process_batch(index: str, items: List[Dict[str, Any]]):
    """Process a batch of paper records and index them in Elasticsearch"""
    documents = []
    for item in items:
        documents.append({
            "_index": index,
            "_id": item["id"],
            "_source": {
                "id": item["id"],
                "title": item["title"],
                "paper_source": item["paper_source"],
                "data_source_id": item["data_source_id"],
                "doi": item["doi"],
                "author_list": process_semicolon_separated_string(item["author_list"]),
                "affiliations": process_semicolon_separated_string(item["affiliations"]),
                "email_addresses": item["email_addresses"],
                "addresses": item["addresses"],
                "research_area": item["research_area"],
                "keywords": item["keywords"],
                "keywords_plus": item["keywords_plus"],
                "reprint_addresses": item["reprint_addresses"],
                "publication_date": item["publication_date"]
            }
        })
    
    if documents:
        es_client.bulk(index, documents)


if __name__ == "__main__":
    # Use a date-based index name for versioning
    current_date = datetime.now()
    index = "papers_20250808"
    
    # Create index with mapping
    logger.info(f"Creating paper index: {index}")
    create_paper_index(index)
    
    # Start syncing with pagination
    logger.info("Starting to read and sync paper data")
    sync_paper_data(batch_size=10000)  # 每批处理10000条记录
    
    logger.info("Completed syncing paper data")
