import pandas as pd
import ast
import requests
import time

def translate_text(texts):
    url = "https://et-platform-dev3.ikchain.com.cn/api/translation/translate"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOjc2LCJkZXZpY2UiOiJkZWZhdWx0LWRldmljZSIsImVmZiI6MTc1Njg5OTM1NTgzMywicm5TdHIiOiJ4M2x2eHAxaW41SVdsQ2NvU0RObUY1SlFRcnlYNXQxMCJ9.Z6fxS-pFc-GW7UPEmeu82G6JFmQLuWuU0CMINsfosXs",
    }
    
    data = {
        "texts": texts,
        "fromLanguage": "en",
        "toLanguage": "zh",
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()
        if result["code"] == 0 and "data" in result:
            return result["data"]["translatedTexts"]
        else:
            print(f"Translation API error: {result}")
            return texts
    except Exception as e:
        print(f"Error during translation: {e}")
        return texts

def clean_list_column(value):
    try:
        # Try to safely evaluate the string as a Python literal
        if isinstance(value, str):
            # Remove any whitespace and check if it starts with [
            value = value.strip()
            if value.startswith('['):
                # Parse the string as a Python literal
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    # Join the list elements with commas
                    return ', '.join(parsed)
        return value
    except:
        # If any error occurs, return the original value
        return value

def process_research_direction(value):
    # First clean the list format
    cleaned_value = clean_list_column(value)
    if not cleaned_value or not isinstance(cleaned_value, str):
        return cleaned_value
        
    # Split by comma and translate each item
    items = [item.strip() for item in cleaned_value.split(',')]
    translated_items = translate_text(items)
    
    # Join translated items back with commas
    return ', '.join(translated_items)

def main():
    # Read the Excel file
    input_file = '../ic_v6(1).xlsx'
    df = pd.read_excel(input_file)
    
    # Process research direction column with translation
    if '研究方向' in df.columns:
        print("Processing and translating 研究方向 column...")
        df['研究方向'] = df['研究方向'].apply(process_research_direction)
        print("Translation completed for 研究方向")
    
    # List of other columns to clean (without translation)
    other_columns = ['l1_domains', 'l2_domains', 'l3_domains', 
                    'major_paper_1_domain', 'major_paper_2_domain', 'major_paper_3_domain',
                    'minor_paper_1_domain', 'minor_paper_2_domain', 'minor_paper_3_domain']
    
    # Clean other columns without translation
    for col in other_columns:
        if col in df.columns:
            print(f"Processing column: {col}")
            df[col] = df[col].apply(clean_list_column)
    
    # Save the processed file
    output_file = 'processed_ic_v6.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Processed file saved as {output_file}")

if __name__ == "__main__":
    main() 