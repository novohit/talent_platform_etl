from etl.operations import query_teachers
from services.es.teacher_service import TeacherService
from logger import logger


def main():
    logger.info("Starting ETL process")
    try:
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

        # Example of different log levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

        # Simulating an error
        # raise Exception("Sample error")

    except Exception as e:
        logger.error(f"Error occurred during ETL process: {str(e)}", exc_info=True)
        raise

    logger.info("ETL process completed successfully")


if __name__ == "__main__":
    main()
