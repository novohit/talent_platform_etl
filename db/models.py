from sqlmodel import Field, SQLModel
from typing import Optional

class Teacher(SQLModel, table=True):
    __tablename__ = "derived_intl_teacher_data"
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: str
    school_name: str
    derived_teacher_name: str
    is_valid: bool