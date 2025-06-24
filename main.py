from etl.operations import query_teachers
from services.es.teacher_service import TeacherService


def main():
    print("Hello from talent-platform-etl!")

    result = TeacherService.remove_by_ids(
        teacher_ids=["6f12da6d-7a78-4b05-aaac-418a7aba7491"]
    )
    print(result)

    teachers = query_teachers()
    for teacher in teachers:
        if not teacher.is_valid:
            print(
                f"Invalid teacher: {teacher.derived_teacher_name} from {teacher.school_name}"
            )


if __name__ == "__main__":
    main()
