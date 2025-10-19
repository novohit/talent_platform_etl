import pandas as pd
from pathlib import Path
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 翻译API配置
url = "https://et-platform-dev3.ikchain.com.cn/api/translation/translate/llm"
headers = {
    "accept": "application/json, text/plain, */*",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOjc2LCJkZXZpY2UiOiJkZWZhdWx0LWRldmljZSIsImVmZiI6MTc1Njg5OTM1NTgzMywicm5TdHIiOiJ4M2x2eHAxaW41SVdsQ2NvU0RObUY1SlFRcnlYNXQxMCJ9.Z6fxS-pFc-GW7UPEmeu82G6JFmQLuWuU0CMINsfosXs",
}

def translate_text(text, from_lang='en', to_lang='zh'):
    """使用API翻译文本"""
    if not text or text.strip() == "":
        return ""
        
    try:
        data = {
            "texts": [text],
            "fromLanguage": from_lang,
            "toLanguage": to_lang,
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0 and result.get("data", {}).get("translatedTexts"):
                return result["data"]["translatedTexts"][0]
        
        print(f"翻译失败: {response.text}")
        return text
    except Exception as e:
        print(f"翻译错误: {str(e)}")
        return text

def translate_column(text, from_lang='en', to_lang='zh'):
    """翻译文本，处理可能的错误"""
    if pd.isna(text) or text.strip() == "":
        return ""
        
    try:
        return translate_text(text, from_lang=from_lang, to_lang=to_lang)
    except Exception as e:
        print(f"翻译错误: {str(e)}")
        return text

def translate_series(series, from_lang='en', to_lang='zh', max_workers=5):
    """使用线程池翻译整个Series"""
    # 过滤掉空值，避免不必要的API调用
    valid_items = series[~series.isna()].to_dict()
    if not valid_items:
        return pd.Series(index=series.index)
        
    # 创建结果字典，初始化为原始值
    results = series.to_dict()
    
    # 使用线程池进行翻译
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建future到索引的映射
        future_to_idx = {
            executor.submit(translate_column, text, from_lang, to_lang): idx
            for idx, text in valid_items.items()
        }
        
        # 使用tqdm显示进度
        total = len(future_to_idx)
        with tqdm(total=total, desc=f"翻译进度") as pbar:
            # 处理完成的任务
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"处理错误 {idx}: {str(e)}")
                pbar.update(1)
    
    return pd.Series(results, index=series.index)

def process_excel():
    """处理Excel文件并翻译指定列"""
    # 设置输入输出路径
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "output" / "power_qiye" / "talent_all_processed_translated.xlsx"
    output_file = project_root / "output" / "power_qiye" / "talent_all_processed_translated_translated.xlsx"
    
    print(f"读取文件: {input_file}")
    
    # 读取Excel文件
    df = pd.read_excel(input_file)
    
    # 需要翻译的列和对应的语言方向
    columns_to_translate = {
        # 'city': ('en', 'zh'),
        # 'country_code': ('en', 'zh'),
        # 'position': ('en', 'zh'),
        # 'about': ('en', 'zh'),
        # 'current_company': ('en', 'zh'),
        'education': ('en', 'zh'),
        'experience': ('en', 'zh'),
    }
    
    # 处理每一列
    for col, (from_lang, to_lang) in columns_to_translate.items():
        if col in df.columns:
            print(f"\n开始翻译 {col} 列...")
            translated_col = f"{col}_translated"
            # 使用多线程翻译
            df[translated_col] = translate_series(
                df[col], 
                from_lang=from_lang, 
                to_lang=to_lang,
                max_workers=16  # 可以根据需要调整线程数
            )
            print(f"{col} 列翻译完成")
            
            # 定期保存中间结果
            temp_file = output_file.parent / f"temp_{output_file.name}"
            df.to_excel(temp_file, index=False, engine='openpyxl')
    
    # 保存最终结果
    print(f"\n保存翻译结果到: {output_file}")
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    # 删除临时文件
    if temp_file.exists():
        temp_file.unlink()
    
    print("处理完成!")

if __name__ == "__main__":
    process_excel()