import pandas as pd
import json
import re
from pathlib import Path

def clean_text(text):
    """Clean text by removing HTML tags and special characters"""
    if pd.isna(text):
        return ""
    
    # Convert to string
    text = str(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '\n', text)
    
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#x2019;', "'")
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    
    # Remove special characters that Excel doesn't like
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

def format_current_company(company_str):
    """Format current company JSON string into human readable format"""
    if pd.isna(company_str):
        return ""
        
    try:
        company_info = json.loads(company_str)
        if not company_info:
            return ""
            
        lines = []
        if company_info.get("name"):
            lines.append(f"公司: {company_info['name']}")
        if company_info.get("title"):
            lines.append(f"职位: {company_info['title']}")
        if company_info.get("location"):
            lines.append(f"地点: {company_info['location']}")
            
        return "\n".join(lines)
    except:
        return "Error: Invalid JSON format"

def format_honors_and_awards(honors_str):
    """Format honors and awards JSON string into human readable format"""
    if pd.isna(honors_str):
        return ""
        
    try:
        honors_list = json.loads(honors_str)
        if not honors_list:
            return ""
            
        formatted_lines = []
        for honor in honors_list:
            lines = []
            if honor.get("title"):
                lines.append(f"奖项: {honor['title']}")
            if honor.get("publication"):
                lines.append(f"颁发机构: {honor['publication']}")
            if honor.get("date"):
                # 处理ISO格式日期，只保留年月日
                date = honor["date"].split("T")[0] if "T" in honor["date"] else honor["date"]
                lines.append(f"获奖时间: {date}")
            if honor.get("description"):
                lines.append(f"描述: {honor['description']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_organizations(organizations_str):
    """Format organizations JSON string into human readable format"""
    if pd.isna(organizations_str):
        return ""
        
    try:
        organizations_list = json.loads(organizations_str)
        if not organizations_list:
            return ""
            
        formatted_lines = []
        for org in organizations_list:
            lines = []
            if org.get("title"):
                lines.append(f"组织: {org['title']}")
            if org.get("membership_type") and org["membership_type"] != "-":
                lines.append(f"职位: {org['membership_type']}")
            if org.get("start_date") and org.get("end_date"):
                lines.append(f"时间: {org['start_date']} - {org['end_date']}")
            elif org.get("start_date"):
                lines.append(f"时间: {org['start_date']} - 至今")
            if org.get("description"):
                lines.append(f"描述: {org['description']}")
            if org.get("membership_number"):
                lines.append(f"会员编号: {org['membership_number']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_volunteer_experience(volunteer_str):
    """Format volunteer experience JSON string into human readable format"""
    if pd.isna(volunteer_str):
        return ""
        
    try:
        volunteer_list = json.loads(volunteer_str)
        if not volunteer_list:
            return ""
            
        formatted_lines = []
        for vol in volunteer_list:
            lines = []
            if vol.get("title"):
                lines.append(f"职位: {vol['title']}")
            if vol.get("subtitle"):
                lines.append(f"组织: {vol['subtitle']}")
            if vol.get("cause"):
                lines.append(f"类型: {vol['cause']}")
            if vol.get("duration"):
                lines.append(f"时间: {vol['duration']}")
            if vol.get("info"):
                lines.append(f"描述: {vol['info']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_certifications(certifications_str):
    """Format certifications JSON string into human readable format"""
    if pd.isna(certifications_str):
        return ""
        
    try:
        certifications_list = json.loads(certifications_str)
        if not certifications_list:
            return ""
            
        formatted_lines = []
        for cert in certifications_list:
            lines = []
            if cert.get("title"):
                lines.append(f"证书名称: {cert['title']}")
            if cert.get("subtitle"):
                lines.append(f"颁发机构: {cert['subtitle']}")
            if cert.get("meta"):
                lines.append(f"时间信息: {cert['meta']}")
            if cert.get("credential_id"):
                lines.append(f"证书编号: {cert['credential_id']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_patents(patents_str):
    """Format patents JSON string into human readable format"""
    if pd.isna(patents_str):
        return ""
        
    try:
        patents_list = json.loads(patents_str)
        if not patents_list:
            return ""
            
        formatted_lines = []
        for patent in patents_list:
            lines = []
            if patent.get("title"):
                lines.append(f"专利名称: {patent['title']}")
            if patent.get("date_issued"):
                lines.append(f"授权日期: {patent['date_issued']}")
            if patent.get("patents_id"):
                lines.append(f"专利号: {patent['patents_id']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_projects(projects_str):
    """Format projects JSON string into human readable format"""
    if pd.isna(projects_str):
        return ""
        
    try:
        projects_list = json.loads(projects_str)
        if not projects_list:
            return ""
            
        formatted_lines = []
        for proj in projects_list:
            lines = []
            if proj.get("title"):
                lines.append(f"项目: {proj['title']}")
            if proj.get("start_date"):
                lines.append(f"开始时间: {proj['start_date']}")
            if proj.get("description"):
                lines.append(f"描述: {proj['description']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_publications(publications_str):
    """Format publications JSON string into human readable format"""
    if pd.isna(publications_str):
        return ""
        
    try:
        publications_list = json.loads(publications_str)
        if not publications_list:
            return ""
            
        formatted_lines = []
        for pub in publications_list:
            lines = []
            if pub.get("title"):
                lines.append(f"标题: {pub['title']}")
            if pub.get("subtitle"):
                lines.append(f"发表于: {pub['subtitle']}")
            if pub.get("date"):
                lines.append(f"日期: {pub['date']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_position(position):
    """Format a single position into human readable format"""
    lines = []
    if position.get("title"):
        lines.append(f"职位: {position['title']}")
    if position.get("subtitle"):
        lines.append(f"公司: {position['subtitle']}")
    if position.get("location"):
        lines.append(f"地点: {position['location']}")
    
    # Handle dates
    start_date = position.get("start_date", "")
    end_date = position.get("end_date", "Present")
    if start_date:
        lines.append(f"时间: {start_date} - {end_date}")
    
    if position.get("description_html"):
        lines.append(f"描述: {position['description_html']}")
        
    return "\n".join(lines)

def format_experience(experience_str):
    """Format experience JSON string into human readable format"""
    if pd.isna(experience_str):
        return ""
        
    try:
        experience_list = json.loads(experience_str)
        if not experience_list:
            return ""
            
        formatted_lines = []
        for exp in experience_list:
            lines = []
            
            # Handle company info
            if exp.get("company"):
                lines.append(f"公司: {exp['company']}")
            if exp.get("title"):
                lines.append(f"职位: {exp['title']}")
            if exp.get("location"):
                lines.append(f"地点: {exp['location']}")
                
            # Handle dates
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "Present")
            if start_date:
                lines.append(f"时间: {start_date} - {end_date}")
            
            # Handle positions if they exist
            if exp.get("positions"):
                lines.append("\n子职位:")
                for pos in exp["positions"]:
                    lines.append("\n" + format_position(pos))
            
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def format_education(education_str):
    """Format education JSON string into human readable format"""
    if pd.isna(education_str):
        return ""
        
    try:
        education_list = json.loads(education_str)
        if not education_list:
            return ""
            
        formatted_lines = []
        for edu in education_list:
            lines = []
            if edu.get("title"):
                lines.append(f"学校: {edu['title']}")
            if edu.get("degree"):
                lines.append(f"学位: {edu['degree']}")
            if edu.get("field"):
                lines.append(f"专业: {edu['field']}")
            if edu.get("start_year") and edu.get("end_year"):
                lines.append(f"时间: {edu['start_year']} - {edu['end_year']}")
            elif edu.get("start_year"):
                lines.append(f"时间: {edu['start_year']} - 至今")
            if edu.get("description"):
                lines.append(f"描述: {edu['description']}")
                
            formatted_lines.append("\n".join(lines))
            
        return "\n\n".join(formatted_lines)
    except:
        return "Error: Invalid JSON format"

def process_file(input_file):
    """Process a single CSV file"""
    print(f"Reading file: {input_file}")
    
    try:
        # Read CSV file with proper encoding
        df = pd.read_csv(input_file, encoding='utf-8')
        
        # Process the dataframe
        process_dataframe(df)
        
        return df
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        return None

def process_dataframe(df):
    """Process a single dataframe"""
    if df is None or df.empty:
        return
    
    # Remove unwanted columns
    columns_to_remove = ['posts', 'groups', 'people_also_viewed', 'recommendations_count', 
    'recommendations', 'followers',
    'connections', 'current_company_company_id', 'input_url',
    'activity', 'banner_image', 'similar_profiles', 'default_avatar',
    'memorialized_account', 'bio_links', 'timestamp', 'input',
    'error', 'error_code', 'warning', 'warning_code',
    'linkedin_id', 'linkedin_num_id', 'urn_id', 'courses'
    ]
    for col in columns_to_remove:
        if col in df.columns:
            print(f"Removing column: {col}")
            df.drop(columns=[col], inplace=True)
    
    # Process columns
    if "education" in df.columns:
        print("Processing education column...")
        df["education"] = df["education"].apply(format_education)
        
    if "experience" in df.columns:
        print("Processing experience column...")
        df["experience"] = df["experience"].apply(format_experience)
        
    if "publications" in df.columns:
        print("Processing publications column...")
        df["publications"] = df["publications"].apply(format_publications)
        
    if "projects" in df.columns:
        print("Processing projects column...")
        df["projects"] = df["projects"].apply(format_projects)
        
    if "patents" in df.columns:
        print("Processing patents column...")
        df["patents"] = df["patents"].apply(format_patents)
        
    if "certifications" in df.columns:
        print("Processing certifications column...")
        df["certifications"] = df["certifications"].apply(format_certifications)
        
    if "volunteer_experience" in df.columns:
        print("Processing volunteer experience column...")
        df["volunteer_experience"] = df["volunteer_experience"].apply(format_volunteer_experience)
        
    if "organizations" in df.columns:
        print("Processing organizations column...")
        df["organizations"] = df["organizations"].apply(format_organizations)
        
    if "honors_and_awards" in df.columns:
        print("Processing honors and awards column...")
        df["honors_and_awards"] = df["honors_and_awards"].apply(format_honors_and_awards)
        
    if "current_company" in df.columns:
        print("Processing current company column...")
        df["current_company"] = df["current_company"].apply(format_current_company)

def main():
    """Process all CSV files in the data directory"""
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Input and output paths
    input_dir = project_root / "data" / "power_qiye"
    output_dir = project_root / "output" / "power_qiye"
    output_file = output_dir / "talent_all_processed.xlsx"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all CSV files in the input directory
    csv_files = list(input_dir.glob("bd_*.csv"))
    
    if not csv_files:
        print("No CSV files found in the input directory")
        return
        
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process all files and collect the results
    all_dfs = []
    for csv_file in csv_files:
        df = process_file(csv_file)
        if df is not None and not df.empty:
            all_dfs.append(df)
    
    if not all_dfs:
        print("No data to save after processing")
        return
        
    # Concatenate all dataframes
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates if any
    if 'linkedin_url' in final_df.columns:
        final_df.drop_duplicates(subset=['linkedin_url'], keep='first', inplace=True)
    
    # Clean all text columns before saving
    text_columns = ['education', 'experience', 'publications', 'projects', 'patents', 
                   'certifications', 'volunteer_experience', 'organizations', 
                   'honors_and_awards', 'current_company']
    
    for col in text_columns:
        if col in final_df.columns:
            final_df[col] = final_df[col].apply(clean_text)
    
    # Save the final result
    print(f"Saving combined results to: {output_file}")
    final_df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Done! Processed {len(csv_files)} files with {len(final_df)} total records")

if __name__ == "__main__":
    main()
