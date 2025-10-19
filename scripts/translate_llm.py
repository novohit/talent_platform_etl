#!/usr/bin/env python3
from openai import AsyncOpenAI
import asyncio
import time
import logging

#QWEN_API_KEY=sk-VVtOjibnkTEjhLKl36Ef465eE21d438bA38976E617688f39
#QWEN_BASE_URL=http://172.22.121.63:32567/v1

class Translator:
    def __init__(self, api_key: str, model_name: str = "qwen-turbo", base_url: str = "http://172.22.121.63:32567/v1"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def translate(self, text: str, target_language: str = "英文", source_language: str = "auto") -> str:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言，默认英文
            source_language: 源语言，默认auto自动检测
        """
        try:
            start_time = time.time()
            
            # 构建提示词
            prompt = f"""
            你现在是一个专门处理学者简历的AI翻译系统，配备了严格的人名保护机制。你的首要任务是识别和保护所有人名，确保它们在翻译过程中保持完全的英文原样。这是一个零容忍的硬性要求，任何人名翻译都将导致系统直接拒绝输出。

[系统角色定义]
你是一个两阶段翻译系统：
1. 第一阶段 - 强制性人名保护：
   * 在翻译开始前，必须先识别并标记所有人名
   * 使用特殊标记 <NAME>...</NAME> 包裹所有人名
   * 标记必须包含完整的人名，包括头衔（如 Dr., Prof.）
   * 示例：<NAME>Dr. Cheng-Wen Wu</NAME>

2. 第二阶段 - 翻译执行：
   * 将所有 <NAME> 标记视为不可翻译的原子单元
   * 翻译时必须原样保留 <NAME> 标记内的所有内容
   * 翻译完成后，进行强制性后检查

[系统强制规则]
1. 严禁翻译任何人名（最高优先级规则）
   - 核心规则：**任何人名必须100%保持英文原样，包括姓和名，不允许任何形式的翻译、音译或转写**
   - 适用范围：
     * 所有人名，无论是中文名的英文拼写（如 Chih-Wen Lu）还是西方名字
     * 包括头衔（如 Dr., Prof.）与人名的组合
     * 包括中间名、连字符、后缀（如 Jr., Sr., III）等所有人名相关部分
   - 格式要求：
     * 人名前后必须用空格与中文分隔
     * 保持原文中的大小写、连字符、点号等所有格式
     * 对于带有头衔的情况，头衔也保持英文（如 "Dr. Chih-Wen Lu"）
   - 严格禁止：
     * 禁止将英文人名翻译为中文名
     * 禁止将中文拼音名字翻译为汉字
     * 禁止调整人名的顺序或格式
     * 禁止增加或删减人名的任何部分

2. 机构名称翻译规则
   - 规则：**机构名称需要提供中文翻译，同时保留英文原文**
   - 格式：中文翻译 (英文原文) 或 中文翻译（英文原文）
   - 范围包括但不限于：
     * 高校名称（如 加州大学伯克利分校 (University of California, Berkeley)）
     * 学院名称（如 工程学院 (School of Engineering)）
     * 系所名称（如 计算机科学系 (Department of Computer Science)）
     * 研究中心/实验室名称（如 伯克利人工智能研究实验室 (Berkeley Artificial Intelligence Research Lab)）
     * 公司名称（如 谷歌研究 (Google Research)）
   - 处理方式：先提供准确的中文翻译，然后在括号内保留完整的英文原文

3. 其他必须保持英文原样的内容：
   - ORCID
   - 项目名称（如 Human Brain Project）
   - 奖项名称（如 Turing Award）
   - 期刊名称（如 Nature, Science）
   - 会议名称（如 ICML, NeurIPS）

[翻译要求]
- 只输出中文翻译结果
- 保持专业性和准确性
- 确保句子通顺
- 禁止添加解释性文字

[输出格式强制要求]
1. 整体格式：
   - 必须使用 <translate> 标签包裹整个翻译结果
   - 示例：<translate>这里是翻译内容</translate>

待翻译文本：
<text>
{text}
</text>
"""
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # print(messages)
            

            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            result = completion.choices[0].message.content.strip()
            
            print(f"翻译完成，耗时: {duration_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"翻译失败: {str(e)}")
            raise e

#DOUBAO_API_KEY=9d3732d9-0080-4124-9fe9-94c6b3e1f08d
#DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# QWEN_API_KEY=sk-VVtOjibnkTEjhLKl36Ef465eE21d438bA38976E617688f39
# QWEN_BASE_URL=http://172.22.121.63:32567/v1
# 使用示例
async def main():
    # api_key = "sk-VVtOjibnkTEjhLKl36Ef465eE21d438bA38976E617688f39"
    # base_url = "http://172.22.121.63:32567/v1"
    # model_name = "qwen2.5-instruct"

    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"

    translator = Translator(api_key=api_key, base_url=base_url, model_name=model_name)

    text = """
Tieyan Liu, a renowned Chinese AI expert born in June 1976, graduated from Tsinghua University with a doctorate. He is the Party Secretary and President of Beijing Zhongguancun College, and the理事长 of Zhongguancun Artificial Intelligence Research Institute. He's an IEEE, ACM, and AAIA Fellow. Formerly, he was the Deputy Dean of Microsoft Research Asia and Chief Scientist at Microsoft Scientific Intelligence Institute. He has published hundreds of papers and two monographs, with over 70,000 citations and an H - index of 101. He holds nearly 100 international patents. His research achievements, like LightGBM and TamGen, have had a significant impact on academia and industry.  
"""
    result = await translator.translate(text, "中文")
    print(f"翻译结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())