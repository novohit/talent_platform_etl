import asyncio
import logging
import os
from pathlib import Path

import aiohttp
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter("%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
from typing import Any, Dict, List

from tenacity import RetryCallState, retry, stop_after_attempt, wait_fixed
from utils.htmlparser import HtmlParser

parser = HtmlParser()
from urllib.parse import quote, unquote, urlparse

# 获取当前文件所在目录，然后构建数据文件的绝对路径
current_dir = Path(__file__).parent
plugin_dir = current_dir.parent  # 上一级目录是插件根目录
csv_path = plugin_dir / "data" / "school_info.csv"
df_school = pd.read_csv(csv_path)
name2domain = {row["school_name"]: row["domain"] for _, row in df_school.iterrows()}


endpoint = os.getenv("ENDPOINT")
coroutine_num = int(os.getenv("COROUTINE_NUM"))
api_key = os.getenv("GOOGLE_API_KEY")
semaphore = asyncio.Semaphore(coroutine_num)


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
async def brightdata_api(query: str) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        payload = {
            "zone": "serp_api1",
            "url": f"https://www.google.com/search?q={query}&brd_json=1",
            "format": "raw",
            "method": "GET",
        }

        try:
            async with session.post(
                endpoint, headers=headers, json=payload, timeout=90
            ) as response:
                response.raise_for_status()
                result = await response.json()
                organic = result.get("organic", "")
                if organic == "":
                    logger.error(f"搜索结果为空：{unquote(query)}")
                return organic
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            raise


async def process_row(row) -> pd.DataFrame:
    async with semaphore:
        paper_author_info_id = row["id"]
        teacher_id = row["teacher_id"]
        raw_data_id = row["raw_data_id"]
        teacher_name = row["derived_teacher_name"]
        school_name = row["school_name"]
        origin_description = row["description"]
        domain = name2domain.get(school_name, "")

        if domain == "":
            q = f"{teacher_name} {school_name} -filetype:pdf -filetype:ppt -filetype:doc -filetype:xls".replace(
                " ", "+"
            )
        else:
            q = f"{teacher_name} {school_name} site:{domain} -filetype:pdf -filetype:ppt -filetype:doc -filetype:xls".replace(
                " ", "+"
            )
        query = quote(q)

        try:
            organic_data = await brightdata_api(query)
            logger.info(f"搜索 {q} 完毕")
        except Exception as e:
            logger.error(f"搜索失败: {q} - {str(e)}")
            return

        task = [fetch_html_with_requests(data.get("link", "")) for data in organic_data]
        html_infos = await asyncio.gather(*task)

        res = []
        for data, html_info in zip(organic_data, html_infos):
            res.append(
                (
                    paper_author_info_id,
                    teacher_id,
                    raw_data_id,
                    teacher_name,
                    school_name,
                    origin_description,
                    data.get("title", ""),
                    data.get("description", ""),
                    html_info,
                    data.get("link", ""),
                    data.get("rank", 0),
                )
            )
        df = pd.DataFrame(
            res,
            columns=[
                "id",
                "teacher_id",
                "raw_data_id",
                "teacher_name",
                "school_name",
                "origin_description",
                "title",
                "description",
                "html_info",
                "link",
                "rank",
            ],
        )
        return df


def return_empty_string_on_retry_error(retry_state: RetryCallState):
    """超过最大重试次数时返回空字符串并记录日志"""
    logger.warning(f"任务失败，已达到最大重试次数: {retry_state.attempt_number}")
    return ""


@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    retry_error_callback=return_empty_string_on_retry_error,
)
async def fetch_html_with_requests(url: str) -> str:
    if url == "":
        return ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status // 100 != 2:
                return "error"

            text = ""
            content = await response.read()
            try_count = 0
            encodings = ["utf-8", "GB2312", "UTF-8-SIG"]
            for encoding in encodings:
                try:
                    text = content.decode(encoding, errors="strict")
                    break  # 成功解码后跳出循环
                except Exception as e:
                    try_count += 1
                    continue
            if try_count == len(encodings):
                return "undecodable"

            cleaned_html = parser.only_skeleton(text)
            logger.info(f"成功获取HTML页面: {url}")
            return cleaned_html
