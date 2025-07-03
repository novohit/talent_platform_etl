#!/usr/bin/env python3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from es.client import es_client
from logger import logger


def read_excel_data(file_path):
    """Read teacher ID and email mapping from Excel file"""
    try:
        df = pd.read_excel(file_path)
        # Convert DataFrame to dictionary for easier lookup
        result = {}
        for _, row in df.iterrows():
            teacher_id = row["teacher_id"]
            email = row["邮箱"]
            if isinstance(teacher_id, (int, float, str)) and not pd.isna(teacher_id):
                result[str(teacher_id)] = str(email)
        return result
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise


def update_teacher_email(teacher_id, new_email):
    """Update teacher email in Elasticsearch"""
    try:
        # Update document by teacher_id

        script = {
            "source": "ctx._source.email = params.email",
            "lang": "painless",
            "params": {"email": new_email},
        }
        query = {"term": {"teacherId.keyword": teacher_id}}

        result = es_client.update_by_query(
            index="teachers_20250630", query=query, script=script
        )

        updated = result.get("updated", 0)
        if updated > 0:
            logger.info(f"Successfully updated email for teacher_id {teacher_id}")
        else:
            logger.warning(f"No document found for teacher_id {teacher_id}")

        return updated

    except Exception as e:
        logger.error(f"Error updating email for teacher_id {teacher_id}: {e}")
        return 0


def main():
    try:
        # Get Excel file path from command line argument
        if len(sys.argv) != 2:
            print("Usage: python update_es_email.py <excel_file_path>")
            sys.exit(1)

        excel_file = sys.argv[1]

        # Read data from Excel
        teacher_data = read_excel_data(excel_file)

        logger.info(teacher_data)
        # Track statistics
        total_updates = 0
        failed_updates = []

        # Process each teacher
        for teacher_id, email in teacher_data.items():
            if not email or email == "nan":
                logger.warning(f"Skipping teacher_id {teacher_id} due to empty email")
                continue

            updated = update_teacher_email(teacher_id, email)
            if updated > 0:
                total_updates += updated
            else:
                failed_updates.append(teacher_id)

        # Print summary
        logger.info(f"Update completed. Total successful updates: {total_updates}")
        if failed_updates:
            logger.warning(
                f"Failed to update {len(failed_updates)} teachers: {failed_updates}"
            )

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)


# PYTHONPATH=$(pwd) uv run scripts/update_es_email.py scripts/wait_update.xlsx
if __name__ == "__main__":
    main()
