from sqlmodel import Field, SQLModel, JSON, Column
from typing import Optional, Dict, Any
from datetime import datetime
import json


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


class ScheduledTaskModel(SQLModel, table=True):
    __tablename__ = "scheduled_tasks"
    
    id: str = Field(primary_key=True)
    name: str = Field(max_length=255)
    plugin_name: str = Field(max_length=100)
    parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    schedule_type: str = Field(max_length=20)  # 'cron', 'interval'
    schedule_config: Dict[str, Any] = Field(sa_column=Column(JSON))
    enabled: bool = Field(default=True)
    
    # 执行状态跟踪
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # 审计字段
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(default="system", max_length=100)
    
    # 任务元数据
    description: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[str] = Field(default=None, max_length=255)  # JSON string
    priority: int = Field(default=5)  # 1-10, 10 is highest
    max_retries: int = Field(default=3)
    timeout: Optional[int] = Field(default=None)  # seconds
