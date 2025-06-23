from etl.operations import query_teachers

def main():
    print("Hello from talent-platform-etl!")
    teachers = query_teachers()
    for teacher in teachers:
        if not teacher.is_valid:
            print(f"Invalid teacher: {teacher.derived_teacher_name} from {teacher.school_name}")

if __name__ == "__main__":
    main()