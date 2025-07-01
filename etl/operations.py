from db.database import engine, get_session
from db.models import Teacher, TeacherDomain


from sqlmodel import SQLModel, select


def create_tables():
    SQLModel.metadata.create_all(engine)


def query_teachers():
    with get_session() as session:
        statement = select(Teacher).limit(100)
        results = session.exec(statement)
        return list(results)


def query_invalid_teachers():
    with get_session() as session:
        statement = select(Teacher).where(Teacher.is_valid == False).limit(10)
        results = session.exec(statement)
        return list(results)

def query_teacher_domain():
    with get_session() as session:
        statement = select(TeacherDomain).limit(10)
        results = session.exec(statement)
        return list(results)