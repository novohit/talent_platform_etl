import os
import pandas as pd
import pymysql
from pathlib import Path

def get_db_connection():
    """Create a database connection"""
    return pymysql.connect(
        host="172.22.121.11",  # Update with your DB host
        port=43200,
        user="zwx",      # Update with your DB user
        password="006af022-f15c-442c-8c56-e71a45d4531e",      # Update with your DB password
        database="personnel-matching-new",  # Update with your DB name
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_existing_linkedin_ids(conn, linkedin_ids):
    """Query database for existing linkedin_num_ids"""
    if not linkedin_ids:
        return set()
        
    cursor = conn.cursor()
    # Convert list to string for IN clause
    ids_str = ','.join(map(str, linkedin_ids))
    query = f"SELECT linkedin_num_id FROM raw_linkedin_profiles WHERE linkedin_num_id IN ({ids_str})"
    cursor.execute(query)
    existing_ids = {str(row['linkedin_num_id']) for row in cursor.fetchall()}
    cursor.close()
    return existing_ids

def save_missing_ids(missing_ids_by_file, file_data_map, output_path):
    """Save missing IDs to a CSV file with id and linkedin_num_id columns"""
    output_data = []
    for file_name, ids in missing_ids_by_file.items():
        # Get the original DataFrame for this file
        df = file_data_map[file_name]
        
        # Filter rows with missing IDs and select only id and linkedin_num_id columns
        # Filter rows with missing IDs, handling potential NaN values
        def check_id(x):
            if pd.isna(x):
                return False
            try:
                return str(int(float(x))) in ids
            except (ValueError, TypeError):
                return False
        
        missing_rows = df[df['linkedin_num_id'].apply(check_id)]
        selected_data = missing_rows[['id', 'linkedin_num_id']].copy()
        selected_data['source_file'] = file_name
        
        # Append to output data
        output_data.append(selected_data)
    
    # Combine all DataFrames and save
    if output_data:
        combined_df = pd.concat(output_data, ignore_index=True)
        # Ensure columns are in the desired order
        combined_df = combined_df[['source_file', 'id', 'linkedin_num_id']]
        combined_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nMissing IDs saved to: {output_path}")

def process_csv_files():
    """Process all CSV files in the power_qiye directory"""
    # Get the data directory path
    data_dir = Path('/Users/novo/code/java/external-talent-backend/src/main/resources/static/企业工程师')
    
    # Store all linkedin_num_ids from CSV files
    all_linkedin_ids = set()
    file_data = {}  # Store file -> linkedin_ids mapping
    
    # Store DataFrames for each file
    file_data_map = {}
    
    # Process each CSV file
    for csv_file in data_dir.glob('*.csv'):
        try:
            # Read CSV file, specify linkedin_num_id as string type
            df = pd.read_csv(csv_file, dtype={'linkedin_num_id': str})
            
            # Get linkedin_num_ids from this file
            if 'linkedin_num_id' in df.columns:
                # Convert to integer string (remove any decimals) and remove any NaN values
                file_linkedin_ids = set()
                for id_ in df['linkedin_num_id'].dropna():
                    try:
                        # Convert to integer and then string, skip if conversion fails
                        file_linkedin_ids.add(str(int(float(id_))))
                    except (ValueError, TypeError):
                        print(f"Warning: Skipping invalid ID value: {id_}")
                all_linkedin_ids.update(file_linkedin_ids)
                file_data[csv_file.name] = file_linkedin_ids
                file_data_map[csv_file.name] = df  # Store DataFrame for later use
                print(f"Processed {csv_file.name}: Found {len(file_linkedin_ids)} LinkedIn IDs")
            else:
                print(f"Warning: {csv_file.name} does not contain linkedin_num_id column")
                
        except Exception as e:
            print(f"Error processing {csv_file.name}: {str(e)}")
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Get existing IDs from database
        existing_ids = get_existing_linkedin_ids(conn, all_linkedin_ids)
        
        # Find missing IDs
        missing_ids = all_linkedin_ids - existing_ids
        
        # Report results
        print("\nResults:")
        print(f"Total unique LinkedIn IDs found: {len(all_linkedin_ids)}")
        print(f"IDs found in database: {len(existing_ids)}")
        print(f"Missing IDs: {len(missing_ids)}")
        
        # Report missing IDs by file and save them
        print("\nMissing IDs by file:")
        missing_ids_by_file = {}
        for file_name, file_ids in file_data.items():
            missing_in_file = file_ids & missing_ids
            if missing_in_file:
                missing_ids_by_file[file_name] = sorted(missing_in_file)
                print(f"\n{file_name}:")
                print(f"Missing IDs count: {len(missing_in_file)}")
                print("Missing IDs:", missing_ids_by_file[file_name])
        
        # Save missing IDs to CSV
        if missing_ids_by_file:
            output_dir = Path('output/missing_ids')
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f'missing_linkedin_ids_{timestamp}.csv'
            save_missing_ids(missing_ids_by_file, file_data_map, output_path)
        
    except Exception as e:
        print(f"Database error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    process_csv_files()
