import pandas as pd
import os

def filter_domains(df):
    """
    Filter dataframe to keep only rows that satisfy both conditions:
    1. major_paper1_domain contains any of the first set of target domains
    2. major_paper2_domain contains any of the second set of target domains
    """
    # Different target domains for each column
    target_domains1 = ['自动化类', '机械类', '力学类', '材料类']  # for major_paper1_domain
    target_domains2 = ['机器人工程']   # for major_paper2_domain
    
    # Create patterns for each set of domains
    pattern1 = '|'.join(target_domains1)
    pattern2 = '|'.join(target_domains2)
    
    # Create masks for both columns with their respective patterns
    mask1 = df['major_paper1_domain'].str.contains(pattern1, na=False)
    mask2 = df['major_paper2_domain'].str.contains(pattern2, na=False)
    
    # Combine masks with AND operation (keep row only if both conditions are met)
    combined_mask = mask1 & mask2
    
    return df[combined_mask]

def main():
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    input_file = os.path.join(project_root, 'data', '机器人工程（算法匹配-机器人）.xlsx')
    output_file = os.path.join(project_root, 'data', '机器人工程（算法匹配-机器人）_filtered.xlsx')

    # Read the Excel file
    print(f"Reading file: {input_file}")
    df = pd.read_excel(input_file)
    
    # Print original row count
    print(f"Original number of rows: {len(df)}")
    
    # Apply domain filtering
    filtered_df = filter_domains(df)
    
    # Print filtered row count
    print(f"Number of rows after filtering: {len(filtered_df)}")
    
    # Save filtered data to new Excel file
    filtered_df.to_excel(output_file, index=False)
    print(f"Filtered data saved to: {output_file}")

if __name__ == "__main__":
    main()
