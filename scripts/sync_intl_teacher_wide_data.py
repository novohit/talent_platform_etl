from es.client import es_client
from db.database import get_session
from db.models import TeacherWide
from sqlmodel import select
from logger import logger
from typing import List
import json
import humps


def sync_teacher_wide_data():
    with get_session() as session:
        statement = select(TeacherWide)
        results = session.exec(statement)
        return list(results)


def create_teacher_index(index):
    es_client.delete_index(index)
    es_client.create_index(index, mapping_file="teacher.json")


def safe_json_loads(json_str, field_name, teacher_id, to_camel=False):
    if not json_str:
        return None
    try:
        data = json.loads(json_str)
        if to_camel:
            if isinstance(data, list):
                return [
                    humps.camelize(item) if isinstance(item, dict) else item
                    for item in data
                ]
            elif isinstance(data, dict):
                return humps.camelize(data)
        return data
    except json.JSONDecodeError:
        logger.warning(
            f"Invalid JSON format in field '{field_name}' for teacher_id={teacher_id}, value: {json_str}"
        )
        return None


def extract_left_bound(ranking):
    if not ranking or not isinstance(ranking, str):
        return 999999

    try:
        ranking = ranking.strip()
        if "-" in ranking:
            # Handle range format (e.g., "101-150")
            left_bound = ranking.split("-")[0].strip()
            return int(left_bound)
        else:
            # Handle single number format (e.g., "50")
            return int(ranking)
    except (ValueError, IndexError):
        return 999999


def get_normalized_title(normalized_title, is_phd):
    if not normalized_title or not normalized_title.strip():
        return "phd" if is_phd else "其他"
    return normalized_title


def safe_split_string(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def process_batch(items: List[TeacherWide]):
    documents = []
    for item in items:
        educations = safe_json_loads(
            item.educations, "educations", item.teacher_id, to_camel=True
        )
        if isinstance(educations, list):
            for edu in educations:
                if isinstance(edu, dict) and "isValid" in edu:
                    edu["isValid"] = bool(edu["isValid"])
                if isinstance(edu, dict) and "isFromOrcid" in edu:
                    edu["isFromOrcid"] = bool(edu["isFromOrcid"])

        employments = safe_json_loads(
            item.employments, "employments", item.teacher_id, to_camel=True
        )
        if isinstance(employments, list):
            for emp in employments:
                if isinstance(emp, dict) and "isValid" in emp:
                    emp["isValid"] = bool(emp["isValid"])
                if isinstance(emp, dict) and "isFromOrcid" in emp:
                    emp["isFromOrcid"] = bool(emp["isFromOrcid"])

        documents.append(
            {
                "_index": "teacher_test",
                "_id": item.teacher_id,
                "_source": {
                    "teacherId": item.teacher_id,
                    "derivedTeacherName": item.derived_teacher_name,
                    "schoolName": item.school_name,
                    "schoolNameEn": item.school_name_en,
                    "collegeName": item.college_name,
                    "email": item.email,
                    "omitDescription": item.omit_description,
                    "researchArea": safe_json_loads(
                        item.research_area, "research_area", item.teacher_id
                    ),
                    "normalizedTitle": get_normalized_title(
                        item.normalized_title, item.is_phd
                    ),
                    "isPhd": item.is_phd,
                    "isChinese": item.is_chinese,
                    "isDomeCooperation": item.is_dome_cooperation,
                    "famousTitles": safe_json_loads(
                        item.famous_titles, "famous_titles", item.teacher_id
                    ),
                    "firstLevel": safe_split_string(item.first_level),
                    "secondLevel": safe_split_string(item.second_level),
                    "region": item.region,
                    "ranking": item.ranking,
                    "fakeRanking": extract_left_bound(item.ranking),
                    "paperNum": item.paper_num,
                    "majorPaper1Domain": safe_json_loads(
                        item.major_paper_1_domain,
                        "major_paper_1_domain",
                        item.teacher_id,
                    ),
                    "minorPaper1Domain": safe_json_loads(
                        item.minor_paper_1_domain,
                        "minor_paper_1_domain",
                        item.teacher_id,
                    ),
                    "majorPaper2Domain": safe_json_loads(
                        item.major_paper_2_domain,
                        "major_paper_2_domain",
                        item.teacher_id,
                    ),
                    "minorPaper2Domain": safe_json_loads(
                        item.minor_paper_2_domain,
                        "minor_paper_2_domain",
                        item.teacher_id,
                    ),
                    "majorPaper3Domain": safe_json_loads(
                        item.major_paper_3_domain,
                        "major_paper_3_domain",
                        item.teacher_id,
                    ),
                    "ageRange": item.age_range,
                    "corporateExperience": item.corporate_experience,
                    "overseasExperience": item.overseas_experience,
                    "paperl2Domains": safe_json_loads(
                        item.paper_l2_domains, "paper_l2_domains", item.teacher_id
                    ),
                    "paperl3Domains": safe_json_loads(
                        item.paper_l3_domains, "paper_l3_domains", item.teacher_id
                    ),
                    "famousTitlesLevel": item.famous_titles_level,
                    "jobTitleLevel": item.job_title_level,
                    "educations": educations,
                    "employments": employments,
                },
            }
        )
    if documents:
        es_client.bulk("teacher_test", documents)


if __name__ == "__main__":
    create_teacher_index("teacher_test")
    logger.info("Starting to reading teacher wide data")
    res = sync_teacher_wide_data()
    total_records = len(res)
    logger.info(f"Total records to process: {total_records}")

    batch_size = 1000
    for i in range(0, total_records, batch_size):
        batch = res[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1}, records {i + 1} to {min(i + batch_size, total_records)}"
        )
        process_batch(batch)

    logger.info("Completed syncing teacher wide data")
