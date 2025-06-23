from db.database import engine, get_session
from db.models import Teacher
from sqlmodel import SQLModel, select

def create_tables():
    SQLModel.metadata.create_all(engine)

def query_teachers():
    with get_session() as session:
        statement = select(Teacher).limit(100)  # Adjust the limit as needed
        results = session.exec(statement)
        return list(results) 