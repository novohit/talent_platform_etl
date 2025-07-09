#!/usr/bin/env python3
"""
MySQL连接测试插件
提供MySQL数据库连接测试和基本操作验证功能
"""

import os
import asyncio
import logging
import pandas as pd
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter("%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
from db.operations import batch_insert, query_into_dataframe
from db.sql_sent import ALL_TEACHERS_SQL, SINGLE_TEACHER_SQL
from core.google_seach import process_row
from core.data_process import process_group


async def _main(teacher_id: str):
    teacher_info = query_into_dataframe(SINGLE_TEACHER_SQL.format(teacher_id=teacher_id))

    for _, row in teacher_info.iterrows():
        search_result = await process_row(row)
        result = await process_group(search_result)
        break

    if isinstance(result, pd.DataFrame):
        batch_insert(result, 'raw_web_html')


def main(teacher_id: str=1, **kwargs):
    asyncio.run(_main(teacher_id))


if __name__ == "__main__":
    main()
