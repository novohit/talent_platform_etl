import pandas as pd
import os

def extract_ids():
    # Get the absolute path to the Excel file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(os.path.dirname(current_dir), "人工智能PDF_teacher_id.xlsx")
    
    # Read the Excel file
    df = pd.read_excel(excel_file)
    
    # Get all IDs and format them with quotes
    ids = [f"'{str(id_)}'" for id_ in df.iloc[:, 0].tolist()]
    
    # Join IDs with commas
    formatted_ids = ",\n".join(ids)
    
    # Write to output file
    output_file = os.path.join(os.path.dirname(current_dir), "output", "teacher_ids.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_ids)
    
    print(f"IDs have been extracted and saved to {output_file}")

if __name__ == "__main__":
    extract_ids() 