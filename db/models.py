from sqlmodel import Field, SQLModel
from typing import Optional


class Teacher(SQLModel, table=True):
    __tablename__ = "derived_intl_teacher_data"
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: str
    school_name: str
    college_name: str
    derived_teacher_name: str
    description: str
    is_valid: bool


class TeacherDomain(SQLModel, table=True):
    __tablename__ = "data_intl_teacher_domains"
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: str
    l1_domain_count: str
    l2_domain_count: str
    l3_domain_count: str
    l1_domains: str
    l2_domains: str
    l3_domains: str
    major_paper_1_domain: str
    minor_paper_1_domain: str
    major_paper_2_domain: str
    minor_paper_2_domain: str
    major_paper_3_domain: str
    minor_paper_3_domain: str


class TeacherWide(SQLModel, table=True):
    __tablename__ = "data_intl_wide_view"
    teacher_id: str = Field(primary_key=True)
    school_name: str
    school_name_en: str
    college_name: str
    derived_teacher_name: str
    email: str
    omit_description: str
    research_area: str
    normalized_title: str
    is_phd: int
    is_chinese: int
    famous_titles: str
    first_level: str
    second_level: str
    region: str
    ranking: str
    age_range: str
    corporate_experience: str
    overseas_experience: str
    major_paper_1_domain: str
    minor_paper_1_domain: str
    major_paper_2_domain: str
    minor_paper_2_domain: str
    major_paper_3_domain: str
    paper_l1_domains: str
    paper_l2_domains: str
    paper_l3_domains: str
    is_dome_cooperation: int
    paper_num: int
    is_paper_CNS: int
    educations: str
    employments: str
    famous_titles_level: float
    job_title_level: float


class Domain(SQLModel, table=True):
    __tablename__ = "domain"
    id: str = Field(primary_key=True)
    name: str
    parent: Optional[str] = None
    level: int
    code: Optional[str] = None
    sort: Optional[int] = None
