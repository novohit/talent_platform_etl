import json
import requests
import os
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def transform_education_experience(education_str: str) -> List[Dict[str, Any]]:
    """
    Transform education experience from Excel format to PDF format
    Empty start_date or end_date will be filled with "未知"
    """
    try:
        # Parse the JSON string to list of dictionaries
        educations = json.loads(education_str) if education_str and not pd.isna(education_str) else []
        
        # Transform each education record
        transformed = []
        for edu in educations:
            transformed.append({
                "startDate": edu.get("start_date") if edu.get("start_date") and pd.notna(edu.get("start_date")) else "未知",
                "endDate": edu.get("end_date") if edu.get("end_date") and pd.notna(edu.get("end_date")) else "未知",
                "organization": edu.get("organization", ""),
                "department": edu.get("department", ""),
                "city": edu.get("city", ""),
                "degree": edu.get("degree", ""),
                "isValid": str(edu.get("is_valid", "true")).lower(),
                "isFromOrcid": str(edu.get("is_from_orcid", "false")).lower()
            })
        return transformed
    except json.JSONDecodeError:
        print(f"Error parsing education experience JSON: {education_str}")
        return []

def transform_employment_experience(employment_str: str) -> List[Dict[str, Any]]:
    """
    Transform employment experience from Excel format (semicolon-separated string) to PDF format
    Handles both Chinese (；) and English (;) semicolons
    """
    if pd.isna(employment_str) or not employment_str.strip():
        return []
        
    # Replace Chinese semicolons with English ones and split
    employment_str = employment_str.replace("；", ";")
    employments = [org.strip() for org in employment_str.split(";") if org.strip()]
    
    return [
        {
            "organization": org,
            "roleTitle": "",  # Since role title is not provided in Excel
            "isValid": "true",
            "isFromOrcid": "false"
        }
        for org in employments
    ]

def parse_array_field(field_value: str) -> List[str]:
    """
    Parse a field that contains an array of values
    
    Args:
        field_value: String representation of an array (e.g. "["value1", "value2"]")
        
    Returns:
        List of strings, empty list if input is invalid
    """
    if pd.isna(field_value):
        return []
        
    try:
        # Try to parse as JSON first
        if isinstance(field_value, str) and field_value.strip().startswith("["):
            return json.loads(field_value)
        # If it's a comma-separated string
        elif isinstance(field_value, str):
            return [item.strip() for item in field_value.split(",") if item.strip()]
        return []
    except json.JSONDecodeError:
        # If JSON parsing fails, fall back to comma splitting
        return [item.strip() for item in field_value.split(",") if item.strip()]
    except Exception:
        return []

def read_excel_data(excel_path: str, nrows: int = 10) -> List[Dict[Any, Any]]:
    """
    Read teacher data from Excel file and transform it to the format needed for PDF generation
    
    Args:
        excel_path: Path to the Excel file
        nrows: Number of rows to read (default: 10)
    """
    # Read Excel file
    print(f"Reading first {nrows} rows from Excel file...")
    df = pd.read_excel(excel_path)
    print(f"Found {len(df)} rows")
    
    teachers_data = []
    for _, row in df.iterrows():
        # Handle NaN values in numeric fields
        citations = row["总引用次数(谷歌学术)"]
        h_index = row["h指数(谷歌学术)"]
        i10_index = row["i10指数(谷歌学术)"]
        
        teacher_data = {
            "teacherId": "",  # Generate or leave empty
            "derivedTeacherName": str(row["姓名"]) if pd.notna(row["姓名"]) else "",
            "schoolName": str(row["任职机构"]) if pd.notna(row["任职机构"]) else "",
            "email": str(row["邮箱"]) if pd.notna(row["邮箱"]) else "",
            "region": str(row["地区"]) if pd.notna(row["地区"]) else "",
            "ageRange": str(row["年龄预测"]) if pd.notna(row["年龄预测"]) else "不详",
            "isChinese": 1 if row["是否华人"] == "是" else 0,
            "famousTitles": parse_array_field(row["荣誉称号"]),
            "googleScholarCitations": {
                "totalCitations": int(citations) if pd.notna(citations) else 0,
                "hIndex": int(h_index) if pd.notna(h_index) else 0,
                "i10Index": int(i10_index) if pd.notna(i10_index) else 0
            },
            "firstLevel": parse_array_field(row["一级学科标签"]),
            "secondLevel": parse_array_field(row["二级学科标签"]),
            "paperl3Domains": parse_array_field(row["三级学科标签"]),
            "majorPaper1Domain": parse_array_field(row["主要一级学科标签"]),
            "minorPaper1Domain": parse_array_field(row["次要一级学科标签"]),
            "majorPaper2Domain": parse_array_field(row["主要二级学科标签"]),
            "minorPaper2Domain": parse_array_field(row["次要二级学科标签"]),
            "majorPaper3Domain": parse_array_field(row["主要三级学科标签"]),
            "minorPaper3Domain": parse_array_field(row["次要三级学科标签"]),
            "employments": transform_employment_experience(str(row["工作经历"]) if pd.notna(row["工作经历"]) else ""),
            "educations": transform_education_experience(str(row["教育经历"]) if pd.notna(row["教育经历"]) else "[]"),
            "omitDescription": str(row["个人简介"]) if pd.notna(row["个人简介"]) else "",
            "chineseDescription": str(row["个人简介_中文"]) if pd.notna(row["个人简介_中文"]) else "",
            "domesticCollaborationSchools": str(row["国内合作学校"]) if pd.notna(row["国内合作学校"]) else "",
            "provinceCollaborationSchools": str(row["省内合作学校"]) if pd.notna(row["省内合作学校"]) else ""
        }
        teachers_data.append(teacher_data)
    
    return teachers_data

def generate_pdf(teacher_data: Dict[Any, Any]) -> bool:
    """
    Generate PDF by sending teacher data to the PDF generation endpoint and save it.
    
    Args:
        teacher_data: Dictionary containing teacher information
        
    Returns:
        bool: True if PDF generation and saving was successful, False otherwise
    """
    url = "http://172.22.121.63:32301/generate-pdf"
    
    # Prepare the request payload
    payload = {
        "teacherData": teacher_data
    }
    
    try:
        # Make the POST request
        response = requests.post(url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            # Create output directory if it doesn't exist
            output_dir = "output/pdfs"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename using teacher name and timestamp
            teacher_name = teacher_data.get("derivedTeacherName", "unknown")
            school_name = teacher_data.get("schoolName", "unknown")
            filename = f"{school_name}_{teacher_name}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Save the PDF content
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"PDF generated and saved successfully at: {filepath}")
            return True
        else:
            print(f"Failed to generate PDF. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        return False
    except IOError as e:
        print(f"Error saving PDF file: {str(e)}")
        return False

def main():
    # Path to your Excel file
    excel_path = "ic_v2.xlsx"
    
    try:
        # Read teacher data from Excel
        teachers_data = read_excel_data(excel_path)
        
        if not teachers_data:
            print("No teacher data found in Excel file")
            return
        
        # Use ThreadPoolExecutor for parallel PDF generation
        # Adjust max_workers based on your system capabilities and needs
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks and store the future objects
            future_to_teacher = {
                executor.submit(generate_pdf, teacher_data): teacher_data
                for teacher_data in teachers_data
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_teacher):
                teacher_data = future_to_teacher[future]
                teacher_name = teacher_data['derivedTeacherName']
                try:
                    success = future.result()
                    if success:
                        print(f"Successfully generated PDF for {teacher_name}")
                    else:
                        print(f"Failed to generate PDF for {teacher_name}")
                except Exception as e:
                    print(f"Error generating PDF for {teacher_name}: {str(e)}")
            
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        return

if __name__ == "__main__":
    main()
