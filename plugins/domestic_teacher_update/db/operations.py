import pandas as pd
import math
import time
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
from typing import Dict, Any, List, Set
from db.mysql import get_connection


def batch_insert(df: pd.DataFrame, table: str, batch_size=1000, max_retries=10, retry_delay=10) -> None:
    df = df.fillna('')
    df = df.replace('', None)
    logger.info(f"待插入数据共 {len(df)} 条")
    
    columns = ', '.join(f'`{col}`' for col in df.columns)
    # 生成占位符
    placeholders = ', '.join(['%s'] * len(df.columns))
    # 构建插入语句
    insert_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    # 生成数据
    data_list = [tuple(row) for row in df.values]
    total = len(data_list)
    num_batches = math.ceil(total / batch_size)
    
    for attempt in range(max_retries):
        with get_connection() as conn:
            try:
                cursor = conn.cursor()

                for i in range(num_batches):
                    start_index = i * batch_size
                    end_index = min(start_index + batch_size, total)
                    batch_data = data_list[start_index:end_index]

                    try:
                        cursor.executemany(insert_query, batch_data)
                    except Exception as batch_error:
                        logger.error(f"插入第 {i+1} 批失败, 共 {len(batch_data)} 条数据，错误：{batch_error}")
                        raise
                # 事务提交
                conn.commit()
                # print("######### 新数据插入操作全部已完成")
                logging.info(f"插入成功数据共 {total} 条")

                break  # 如果成功，则跳出重试循环
            except Exception as e:
                logger.error(f"OperationalError: {e}, Attempt {attempt + 1}/{max_retries}")
                # 回滚事务
                conn.rollback()

                # 如果未达到最大重试次数，等待一段时间后重试
                if attempt + 1 < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("已达到最大重试次数，操作失败")
            finally:
                # 关闭游标和连接
                if 'cursor' in locals() and cursor:
                    cursor.close()


def query_into_dataframe(sql_query: str) -> pd.DataFrame:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # 获取列名和数据
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        
        # 手动构建DataFrame
        df = pd.DataFrame(data, columns=columns)
        
    return df
