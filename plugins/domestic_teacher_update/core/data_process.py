import json
import os
import asyncio
import pandas as pd
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter("%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
from utils.llms import duplicate_llm, get_llm_response, contains_english, profile_name_prompt_v4
from utils.check_name_match import check_name_match

coroutine_num = int(os.getenv('COROUTINE_NUM'))
semaphore = asyncio.Semaphore(coroutine_num)


async def process_group(group) -> pd.DataFrame:
    async with semaphore:
        group["is_profile"] = 0
        group["extracted_teacher_name"] = ""
        group["is_repeat"] = 0
        group["is_name_valid"] = 0
        group = group.reset_index(drop=True)
        for i in range(len(group)):
            html_info = "" if pd.isna(group.loc[i, "html_info"]) else group.loc[i, "html_info"]
            teacher_name = group.loc[i, "teacher_name"]
            origin_description = group.loc[i, "origin_description"]

            if html_info != "":
                if len(html_info.replace("\n", "").replace(" ", "")) > 100:
                    # html_md = h.handle(html_info)
                    json_str = await get_llm_response(profile_name_prompt_v4.format(text=html_info[:18000]))
                    # logger.info("成功获得大模型的结果")
                    try:
                        if json_str.replace(" ", "") != "":
                            pre_index = json_str.find("{")
                            post_index = json_str.find("}")
                            json_str = json_str[pre_index: post_index + 1].strip().replace("\n", "")
                            json_str.replace("True", "true")
                            json_str.replace("False", "false")

                            json_data = json.loads(json_str)
                            group.loc[i, "is_profile"] = 1 if json_data["is_profile"] else 0
                            group.loc[i, "extracted_teacher_name"] = json_data["name"].strip() if json_data["name"] else ""
                            if contains_english(group.loc[i, "extracted_teacher_name"])==False:
                                group.loc[i, "extracted_teacher_name"] = group.loc[i, "extracted_teacher_name"].replace(" ", "").replace('\u3000', '')
                            if contains_english(teacher_name)==False:
                                teacher_name = teacher_name.replace(" ", "").replace('\u3000', '')

                            if teacher_name.lower() == group.loc[i, "extracted_teacher_name"].lower():
                                group.loc[i, "is_name_valid"] = 1
                            else:
                                if check_name_match(teacher_name, group.loc[i, "extracted_teacher_name"]):
                                    group.loc[i, "is_name_valid"] = 2
                                else:
                                    group.loc[i, "is_name_valid"] = 0
                    except Exception as e:
                        # print(json_str)
                        # print(group.loc[i, "link"])
                        logger.error(f"解析JSON失败: {str(e)} 字符串为: {json_str}")
                    
                    if group.loc[i, "is_profile"] == 1:
                        is_repeat = await duplicate_llm(origin_description.replace('?', '')[:12000], html_info.replace('?', '')[:12000], teacher_name, group.loc[i, "extracted_teacher_name"])
                        if is_repeat:
                            group.loc[i, "is_repeat"] = 1
                            break
                        
        datas = [(row["teacher_id"], row["raw_data_id"], row["teacher_name"], row["html_info"], row["is_profile"], row["extracted_teacher_name"], row["is_name_valid"], row["link"], 1, 1) for _, row in group.iterrows() if row["is_repeat"] == 1]
        if datas:
            df = pd.DataFrame(datas, columns=['teacher_id', "raw_data_id", 'derived_teacher_name', 'html_info', 'is_profile', 'extracted_teacher_name', 'is_name_valid', 'link', 'is_link_valid', 'is_from_web'])

            return df
        else:
            return None

