import pandas as pd
import json
from typing import List, Dict

def format_experience(experience_json: str) -> str:
    """
    将experience JSON字符串格式化为规范的工作经历字符串
    """
    if not experience_json or pd.isna(experience_json):
        return ""
    
    try:
        experiences = json.loads(experience_json)
        if not experiences:
            return ""
        
        formatted_lines = []
        for exp in experiences:
            company = exp.get('company', '')
            duration = exp.get('duration', '')
            positions = exp.get('positions', [])
            
            # 处理每个职位
            for pos in positions:
                title = pos.get('title', '')
                start_date = pos.get('start_date', '')
                end_date = pos.get('end_date', '')
                location = pos.get('location', '')
                
                position_line = f"{company} | {title}"
                if start_date or end_date:
                    position_line += f" | {start_date} - {end_date}"
                if location:
                    position_line += f" | {location}"
                    
                formatted_lines.append(position_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析错误: {str(e)}")
        return ""

def format_education(education_json: str) -> str:
    """
    将education JSON字符串格式化为规范的教育经历字符串
    """
    if not education_json or pd.isna(education_json):
        return ""
    
    try:
        educations = json.loads(education_json)
        if not educations:
            return ""
        
        formatted_lines = []
        for edu in educations:
            school = edu.get('title', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')
            start_year = edu.get('start_year', '')
            end_year = edu.get('end_year', '')
            
            # 构建教育经历字符串
            edu_line = f"{school} | {degree}"
            if field:
                edu_line += f" | {field}"
            if start_year or end_year:
                edu_line += f" | {start_year} - {end_year}"
                
            formatted_lines.append(edu_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析教育经历错误: {str(e)}")
        return ""

def format_certification(certification_json: str) -> str:
    """
    将certification JSON字符串格式化为规范的证书信息字符串
    """
    if not certification_json or pd.isna(certification_json):
        return ""
    
    try:
        certifications = json.loads(certification_json)
        if not certifications:
            return ""
        
        formatted_lines = []
        for cert in certifications:
            title = cert.get('title', '')
            org = cert.get('subtitle', '')
            meta = cert.get('meta', '')
            
            # 构建证书信息字符串
            cert_line = f"{title}"
            if org:
                cert_line += f" | {org}"
            if meta:
                cert_line += f" | {meta}"
                
            formatted_lines.append(cert_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析证书信息错误: {str(e)}")
        return ""

def format_publication(publication_json: str) -> str:
    """
    将publication JSON字符串格式化为规范的发表文献信息字符串
    """
    if not publication_json or pd.isna(publication_json):
        return ""
    
    try:
        publications = json.loads(publication_json)
        if not publications:
            return ""
        
        formatted_lines = []
        for pub in publications:
            title = pub.get('title', '')
            journal = pub.get('subtitle', '')
            date = pub.get('date', '')
            
            # 构建发表文献信息字符串
            pub_line = f"{title}"
            if journal:
                # 处理期刊名称，如果有多个名称（用逗号分隔），只取第一个
                journal = journal.split(',')[0]
                pub_line += f" | {journal}"
            if date:
                pub_line += f" | {date}"
                
            formatted_lines.append(pub_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析发表文献信息错误: {str(e)}")
        return ""

def format_patent(patent_json: str) -> str:
    """
    将patent JSON字符串格式化为规范的专利信息字符串
    """
    if not patent_json or pd.isna(patent_json):
        return ""
    
    try:
        patents = json.loads(patent_json)
        if not patents:
            return ""
        
        formatted_lines = []
        for pat in patents:
            title = pat.get('title', '')
            patent_id = pat.get('patents_id', '')
            date_issued = pat.get('date_issued', '')
            description = pat.get('description', '')
            
            # 构建专利信息字符串
            pat_line = f"{title}"
            if patent_id:
                # 如果专利号包含国家代码，保留完整信息
                pat_line += f" | {patent_id}"
            if date_issued:
                pat_line += f" | {date_issued}"
            if description:
                pat_line += f" | {description}"
                
            formatted_lines.append(pat_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析专利信息错误: {str(e)}")
        return ""

def format_project(project_json: str) -> str:
    """
    将project JSON字符串格式化为规范的项目经历信息字符串
    """
    if not project_json or pd.isna(project_json):
        return ""
    
    try:
        projects = json.loads(project_json)
        if not projects:
            return ""
        
        formatted_lines = []
        for proj in projects:
            title = proj.get('title', '')
            description = proj.get('description', '')
            
            # 构建项目信息字符串
            proj_line = f"{title}"
            if description:
                # 将描述中的句号替换为分隔符，使其更易读
                description = description.replace('. ', ' | ')
                proj_line += f" | {description}"
                
            formatted_lines.append(proj_line)
                
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"解析项目经历信息错误: {str(e)}")
        return ""

def format_current_company(company_json: str) -> str:
    """
    将current_company JSON字符串格式化为规范的当前公司信息字符串
    """
    if not company_json or pd.isna(company_json):
        return ""
    
    try:
        company = json.loads(company_json)
        if not company:
            return ""
        
        # 提取所有可能的字段
        name = company.get('name', '')
        title = company.get('title', '')
        location = company.get('location', '')
        
        # 构建当前公司信息字符串
        company_line = []
        if name:
            company_line.append(name)
        if title:
            company_line.append(title)
        if location:
            company_line.append(location)
            
        return " | ".join(company_line)
    except Exception as e:
        print(f"解析当前公司信息错误: {str(e)}")
        return ""

def process_csv(input_file: str, output_file: str):
    """
    处理CSV文件，添加格式化的工作经历、教育经历、证书信息、发表文献、专利信息、项目经历和当前公司信息列
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(input_file)
        
        # 添加新的工作经历列
        df['formatted_experience'] = df['experience'].apply(format_experience)
        
        # 添加新的教育经历列
        df['formatted_education'] = df['education'].apply(format_education)
        
        # 添加新的证书信息列
        df['formatted_certification'] = df['certifications'].apply(format_certification)
        
        # 添加新的发表文献列
        df['formatted_publication'] = df['publications'].apply(format_publication)
        
        # 添加新的专利信息列
        df['formatted_patent'] = df['patents'].apply(format_patent)
        
        # 添加新的项目经历列
        df['formatted_project'] = df['projects'].apply(format_project)
        
        # 添加新的当前公司信息列
        df['formatted_current_company'] = df['current_company'].apply(format_current_company)
        
        # 保存结果
        df.to_csv(output_file, index=False)
        print(f"处理完成，结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")

if __name__ == "__main__":
    input_file = "data/bd_20250918_030343_0.csv"
    output_file = "output/bd_20250918_030343_0.csv"
    process_csv(input_file, output_file)