#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from typing import List, Dict
import logging
from dataclasses import dataclass

@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model_name: str

    def get_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_linkedin_data(file_path: str) -> pd.DataFrame:
    """加载LinkedIn数据"""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"成功加载数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        logging.error(f"加载数据失败: {str(e)}")
        raise

def analyze_profile(profile: Dict, llm: LLMConfig) -> bool:
    """使用大模型分析个人信息是否属于AI领域"""
    import requests
    
    # 构建提示词
    prompt = f"""请分析以下LinkedIn个人信息，判断此人是否为人工智能领域的专业人士。
    只需要回答"是"或"否"。

    个人信息：
    工作经历：{profile.get('experience', '')}
    教育背景：{profile.get('education', '')}
    技能：{profile.get('skills', '')}
    """

    try:
        response = requests.post(
            f"{llm.base_url}/chat/completions",
            headers=llm.get_headers(),
            json={
                "model": llm.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content'].strip().lower()
            return '是' in answer
        else:
            logging.error(f"API调用失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"分析个人信息时发生错误: {str(e)}")
        return False

def main():
    setup_logging()
    
    # 配置大模型
    llm = LLMConfig(
        api_key="9d3732d9-0080-4124-9fe9-94c6b3e1f08d",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        model_name="doubao-1-5-pro-32k-250115"
    )
    
    # 加载数据
    input_file = "data/bd_20250901_093139_0.csv"  # 输入文件路径
    output_file = "output/ai_profiles.csv"  # 输出文件路径
    
    df = load_linkedin_data(input_file)
    
    # 分析每个档案
    ai_profiles = []
    total = len(df)
    
    for idx, row in df.iterrows():
        profile = {
            'experience': row.get('experience', ''),
            'education': row.get('education', ''),
            'skills': row.get('skills', '')
        }
        
        logging.info(f"正在处理第 {idx + 1}/{total} 条记录...")
        
        if analyze_profile(profile, llm):
            ai_profiles.append(row)
    
    # 保存结果
    if ai_profiles:
        result_df = pd.DataFrame(ai_profiles)
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        logging.info(f"处理完成，共找到 {len(ai_profiles)} 条AI领域的档案")
    else:
        logging.warning("未找到任何AI领域的档案")

if __name__ == "__main__":
    main()
