import ast
import os
import time
from pathlib import Path

import pandas as pd
import pymysql
import requests
from pymysql import Error


def translate_text(texts):
    url = "https://et-platform-dev3.ikchain.com.cn/api/translation/translate"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOjExLCJkZXZpY2UiOiJkZWZhdWx0LWRldmljZSIsImVmZiI6MTc1ODg3MTg5NTMzMywicm5TdHIiOiJrZnZ4M3FQVGphcElhOFQyRUxGY1l1Y3pnWG1nd3R2QiJ9.SdXifFdfigts1hJdaXYSKn2SVY99U3Ehgn2HeryxUog",
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
            if value.startswith("["):
                # Parse the string as a Python literal
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    # Join the list elements with commas
                    return ", ".join(parsed)
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
    items = [item.strip() for item in cleaned_value.split(",")]
    translated_items = translate_text(items)

    # Join translated items back with commas
    return ", ".join(translated_items)


def get_file_extension(filename):
    """Get the file extension from a filename."""
    return str(filename).lower().split(".")[-1]


def get_data_file(filename):
    """Get file path from data directory."""
    # Try both relative and absolute data directory paths
    data_dirs = [Path("../data"), Path("./data")]

    for data_dir in data_dirs:
        if data_dir.exists():
            file_path = data_dir / filename
            if file_path.exists():
                return file_path

    raise FileNotFoundError(f"Could not find file '{filename}' in data directory")


def read_file(input_file):
    """Read data from either CSV or Excel file."""
    ext = get_file_extension(input_file)
    print(f"Reading {ext.upper()} file: {input_file}")

    if ext == "csv":
        return pd.read_csv(input_file)
    elif ext in ["xlsx", "xls"]:
        return pd.read_excel(input_file)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def save_file(df, output_file):
    """Save data to either CSV or Excel file."""
    ext = get_file_extension(output_file)
    print(f"Saving as {ext.upper()} file: {output_file}")

    if ext == "csv":
        df.to_csv(output_file, index=False)
    elif ext in ["xlsx", "xls"]:
        df.to_excel(output_file, index=False)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def remove_columns(df, columns_to_remove):
    """Remove specified columns from the dataframe if they exist."""
    existing_columns = [col for col in columns_to_remove if col in df.columns]
    if existing_columns:
        print(f"Removing columns: {', '.join(existing_columns)}")
        df.drop(columns=existing_columns, inplace=True)
    return df


def rename_columns(df, column_mapping):
    """Rename columns based on the provided mapping."""
    existing_columns = {
        old: new for old, new in column_mapping.items() if old in df.columns
    }
    if existing_columns:
        print(f"Renaming columns: {existing_columns}")
        df.rename(columns=existing_columns, inplace=True)
    return df


def get_db_connection():
    """Create database connection."""
    try:
        connection = pymysql.connect(
            host="172.22.121.11",
            port=43200,
            database="personnel-matching-new",
            user="zwx",
            password="006af022-f15c-442c-8c56-e71a45d4531e",
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None


def fetch_google_scholar_info(df):
    """Fetch Google Scholar information from database."""
    if "姓名" not in df.columns or "学校（英文）" not in df.columns:
        print("Warning: Required columns not found for Google Scholar lookup")
        return df

    connection = get_db_connection()
    if not connection:
        print("Warning: Could not connect to database, skipping Google Scholar lookup")
        return df

    try:
        cursor = connection.cursor()
        # 创建新列
        df["总引用次数(谷歌学术)"] = None
        df["h指数(谷歌学术)"] = None
        df["i10指数(谷歌学术)"] = None

        # 对每行进行查询
        for index, row in df.iterrows():
            author = row["姓名"]
            affiliation = row["学校（英文）"]

            if pd.isna(author) or pd.isna(affiliation):
                continue

            query = """
            SELECT total_times_cited, h_index, i10_index 
            FROM raw_intl_google_scholar_data 
            WHERE author_list = %s AND school_name = %s
            LIMIT 1
            """
            cursor.execute(query, (author, affiliation))
            result = cursor.fetchone()

            if result:
                df.at[index, "总引用次数(谷歌学术)"] = result[0]
                df.at[index, "h指数(谷歌学术)"] = result[1]
                df.at[index, "i10指数(谷歌学术)"] = result[2]

            # 每100行打印一次进度
            if index % 100 == 0:
                print(f"Processed {index} rows for Google Scholar info...")

        print("Completed Google Scholar info lookup")
        return df

    except Error as e:
        print(f"Error executing database query: {e}")
        return df
    finally:
        if connection:
            cursor.close()
            connection.close()


def fetch_english_school_names(df):
    """Fetch English school names from database for each teacher_id."""
    if "teacher_id" not in df.columns:
        print(
            "Warning: teacher_id column not found, skipping English school name lookup"
        )
        return df

    connection = get_db_connection()
    if not connection:
        print(
            "Warning: Could not connect to database, skipping English school name lookup"
        )
        return df

    try:
        cursor = connection.cursor()
        # 创建新列
        df["所在单位（英文）"] = None

        # 对每个teacher_id进行查询
        for index, row in df.iterrows():
            teacher_id = row["teacher_id"]
            if pd.isna(teacher_id):
                continue

            query = """
            SELECT extracted_school_name 
            FROM derived_intl_school_name 
            WHERE teacher_id = %s
            """
            cursor.execute(query, (teacher_id,))
            result = cursor.fetchone()

            if result:
                df.at[index, "所在单位（英文）"] = result[0]

            # 每100行打印一次进度
            if index % 100 == 0:
                print(f"Processed {index} rows...")

        print("Completed English school name lookup")
        return df

    except Error as e:
        print(f"Error executing database query: {e}")
        return df
    finally:
        if connection:
            cursor.close()
            connection.close()


def process_is_chinese(df):
    """Process is_chinese/是否华人 column, convert 0/1 to 非华裔/华裔."""

    def convert_chinese_status(value):
        # 处理数字和字符串形式的0和1
        if pd.isna(value):
            return value
        str_value = str(value).strip()
        if str_value in ["1", "1.0"]:
            return "华裔"
        elif str_value in ["0", "0.0"]:
            return "非华裔"
        return value

    # 检查并处理可能的列名
    chinese_columns = ["is_chinese", "是否华人"]
    for col in chinese_columns:
        if col in df.columns:
            print(f"Processing {col} column...")
            df[col] = df[col].apply(convert_chinese_status)
            if col == "是否华人":  # 如果是中文列名，重命名为统一的英文列名
                df["is_chinese"] = df[col]
                df.drop(columns=[col], inplace=True)
            break  # 找到并处理一个列后就退出
    return df


def main():
    try:
        # Fixed input filename
        filename = "量子科技申请火炬_processed_processed.xlsx"

        # Get file path from data directory
        input_file = get_data_file(filename)

        # Read the input file
        df = read_file(input_file)

        # Columns to remove
        columns_to_remove = [
            "一级标签计数",
            "二级标签计数",
            "三级标签计数",
            "db_teacher_id",
            "db_school_name",
            "db_college_name",
            "db_derived_teacher_name",
            "db_description",
            "school_match",
            "teacher_id个人简介",
            "teacher_id论文ID",
            "db_teacher_id论文ID",
            "is_same",
            "paper_inter_len",
            "l1_domains",
            "l2_domains",
            "l3_domains",
            "一级标签列表",
            "二级标签列表",
            "三级标签列表",
        ]

        # Remove specified columns
        df = remove_columns(df, columns_to_remove)

        # Process research direction column with translation
        # if "研究方向" in df.columns:
        #     print("Processing and translating 研究方向 column...")
        #     df["研究方向"] = df["研究方向"].apply(process_research_direction)
        #     print("Translation completed for 研究方向")

        # List of other columns to clean (without translation)
        other_columns = [
            "荣誉称号",
            "一级标签列表",
            "二级标签列表",
            "三级标签列表",
            "主要一级标签",
            "主要二级标签",
            "主要三级标签",
            "次要一级标签",
            "次要二级标签",
            "次要三级标签",
            "major_paper_1_domain",
            "minor_paper_1_domain",
            "major_paper_2_domain",
            "minor_paper_2_domain",
            "major_paper_3_domain",
            "minor_paper_3_domain",
        ]

        # Clean other columns without translation
        for col in other_columns:
            if col in df.columns:
                print(f"Processing column: {col}")
                df[col] = df[col].apply(clean_list_column)

        # Process is_chinese column
        df = process_is_chinese(df)

        # Fetch English school names from database
        df = fetch_english_school_names(df)

        # Fetch Google Scholar information
        df = fetch_google_scholar_info(df)

        # Column mapping for renaming (after all processing is done)
        column_mapping = {
            "major_paper_1_domain": "主要一级学科",
            "major_paper1_domain": "主要一级学科",
            "major_paper_2_domain": "主要二级学科",
            "major_paper2_domain": "主要二级学科",
            "major_paper_3_domain": "主要研究方向",
            "major_paper3_domain": "主要研究方向",
            "minor_paper_1_domain": "次要一级学科",
            "minor_paper1_domain": "次要一级学科",
            "minor_paper_2_domain": "次要二级学科",
            "minor_paper2_domain": "次要二级学科",
            "minor_paper3_domain": "次要研究方向",
            "minor_paper_3_domain": "次要研究方向",
            "主要一级标签": "主要一级学科",
            "主要二级标签": "主要二级学科",
            "主要三级标签": "主要研究方向",
            "次要一级标签": "次要一级学科",
            "次要二级标签": "次要二级学科",
            "次要三级标签": "次要研究方向",
            "teacher_name": "姓名",
            "school_name": "学校",
            "school_name_en": "学校（英文）",
            "college_name": "学院",
            "title": "职称",
            "description": "个人简介",
            "is_chinese": "是否华裔",
            "is_phd": "是否博士生",
            "任职机构": "所在单位",
            "荣誉称号": "荣誉",
            "地区": "国家地区",
            "个人简介": "英文简介",
            "research_area": "研究方向",
            "omit_description": "英文简介",
            "个人简介_中文": "中文简介",
            "chinese_description": "中文简介",
            "educations": "教育经历",
            "employments": "工作经历",
            "paper_num": "论文数量",
            "email": "邮箱",
            "region": "国家地区",
            "corporate_experience": "企业经历",
            "overseas_experience": "海外经历",
            "age_range": "年龄预测",
        }

        # Rename columns after all processing
        df = rename_columns(df, column_mapping)

        # Generate output file name
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        input_path = Path(input_file)
        output_file = output_dir / f"{input_path.stem}_processed{input_path.suffix}"

        # Save the processed file
        save_file(df, output_file)
        print("Processing completed successfully!")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
