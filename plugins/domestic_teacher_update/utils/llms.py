duplicate_prompt=  """
你的任务是判断给定的两份简介是否为同一份简介。请仔细阅读以下信息，并按照指示进行判断。
教师名称:
<teacher_name>
{teacher_name}
</teacher_name>
提取的教师名称:
<extracted_teacher_name>
{extracted_teacher_name}
</extracted_teacher_name>
判断教师名称是否一致的规则：
若提取的教师名称包含教师名称中的关键信息（如全名等），则认为是可能同一个名称。若提取的教师名称存在缩写、别名等，但能明显对应到教师名称，则也认为是可能同一个名称。
教师简介:
<origin_description>
{origin_description}
</origin_description>
网页简介:
<html_info>
{html_info}
</html_info>
判断简介是否一致的规则：
1. 对比两者的关键信息，如工作经历、研究方向、主要成就、论文、专利、项目等。若关键信息匹配，则认为简介一致。
2. 考虑信息的完整性，若一个简介包含另一个简介的(工作经历、研究方向、主要成就、论文、专利、项目)，可认为简介一致。
3. 注意信息的时效性，若因时间差异导致部分信息不同(职称、成就、工作经历等)，但核心内容相符，认为简介一致。
4. 如果除去名称相同,只有通用的职称（教授、副教授、讲师、研究员、副研究员等等）相像,则认为不一致
注意事项：
1. 只有一定能判断为同一个简历的才返回True,不是或可能都返回Flase
请在<思考>标签中详细分析判断过程，考虑教师名称是否一致以及简介是否一致。然后在<判断>标签中给出你的最终判断，使用“True”或“Flase”。
<思考>
[在此详细分析判断过程]
</思考>
<判断>
[在此给出“True”或“False”的判断]
</判断>
请确保你的判断客观公正，并基于给定的规则。
"""
profile_name_prompt_v4 =  """
你的任务是根据给定的网页内容，完成教师主页判断任务和姓名提取任务。
以下是网页内容：
<网页内容>
{text}
</网页内容>
### 教师主页判断任务
判断网页内容是否是关于单个人的个人介绍。当且仅当符合【通过标准】且不符合【排除标准】时输出true，否则输出false。
【通过条件】网页内容包含以下至少一项：
- 身份标识（姓名 + 职位/院系）
- 学术履历（教育背景/职称变迁）
- 科研成果/项目/专利
- 研究领域描述
- 荣誉奖项/学术任命
- 第一人称自述
- 第三人称介绍

【排除标准】出现任意即无效：
- 新闻报告风格的个人介绍
- 团队、工作室介绍类型的个人介绍
- 招聘、联系、加入条件类型的个人介绍
- 实验室、平台、论文、项目介绍类型的个人介绍

### 姓名提取任务
当网页内容是关于单个人的个人介绍时，提取出该教师的姓名，如果不是，输出false。
1. 仅保留完整姓名原文
2. 过滤所有头衔（例如：Professor、PhD、Mr、Miss、Dr、President、MD等称呼、头衔、职位、所属）
3. 存在个人教师简体字、繁体字名字和其他语言的姓名混合，优先给出简体字、繁体字名称。
4. 不需要翻译，只需要原文(如拼音翻译为汉字，英语翻译为中文)
5. 只提取返回该网页内容介绍的老师的名称

### 最终输出
请返回严格遵循的JSON格式：
{{
"is_profile": [true/false],
"name": [过滤后的纯姓名/false]
}}
（仅返回该JSON对象，无其他内容）

### 注意事项
严格按照上述JSON格式返回，不要携带任何其他信息。
请直接输出符合要求的JSON对象。
"""

import os
import asyncio
import re
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter("%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.getenv('DOUBAO_API_KEY'),
    base_url=os.getenv('DOUBAO_BASE_URL')
)


@retry(stop=stop_after_attempt(500), wait=wait_fixed(1))
async def get_llm_response(prompt):
    messages = [
        {
            "role": "system",
            "content": '',
        },
        {
            "role": "user",
            "content": prompt,
        }
    ]
    try:
        logger.info("正在调用大模型")
        completion = await client.chat.completions.create(
            # model="qwen2.5-instruct",
            model=os.getenv('DOUBAO_MODEL_NAME'),
            # model="qwen2.5-instruct-6-54-55",
            messages=messages,
        )
        text = completion.choices[-1].message.content
        # print(text)
        return text
    # except asyncio.TimeoutError:
    except Exception as e:
        logger.error("请求超时，正在重试...")
        raise


async def duplicate_llm(des1, des2, teacher_name, extracted_teacher_name):
    prompt = duplicate_prompt.format(teacher_name=teacher_name, extracted_teacher_name=extracted_teacher_name, origin_description=des1, html_info=des2)
    try:
        result = await get_llm_response(prompt)
    except Exception as e:  # 捕获所有异常
        logger.error(f"请求失败，出现异常：{e}. 返回空字符串。")
        exit(1)
    if 'True' in result:
        return True
    else:
        return False


def contains_english(text):
    # 使用正则表达式匹配 ASCII 字母
    pattern = re.compile(r'[a-zA-Z]')
    return bool(pattern.search(text))
