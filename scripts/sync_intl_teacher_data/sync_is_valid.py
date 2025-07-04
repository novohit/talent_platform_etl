from talent_platform.etl.operations import query_invalid_teachers, query_teacher_domain
from talent_platform.services.es.teacher_service import TeacherService
from talent_platform.logger import logger


def remove_invalid_teachers():
    invalid_teachers = query_invalid_teachers()
    # 收集teacher_id
    teacher_ids = [teacher.teacher_id for teacher in invalid_teachers]
    # batch size 100
    for i in range(0, len(teacher_ids), 100):
        batch_teacher_ids = teacher_ids[i : i + 100]
        # 调用es删除
        result = TeacherService.remove_by_ids(batch_teacher_ids)
        logger.info(result)


def sync_teacher_domain():
    teacher_domains = query_teacher_domain()
    for teacher_domain in teacher_domains:
        print(teacher_domain)


# PYTHONPATH=$(pwd) uv run scripts/sync_intl_teacher_data/sync_is_valid.py
if __name__ == "__main__":
    remove_invalid_teachers()
    # sync_teacher_domain()
