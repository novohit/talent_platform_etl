import os
from sqlmodel import Session, create_engine

from talent_platform.config import config


# 通过环境变量控制 SQL 日志输出
SQL_ECHO = os.getenv('SQL_ECHO', 'false').lower() in ('true', '1', 'yes')

engine = create_engine(config.DATABASE_URL, echo=SQL_ECHO)

def get_scheduler_db_engine():
    return create_engine(config.DOMAIN_TREE_DATABASE_URL, echo=SQL_ECHO)

def get_domain_tree_engine():
    return create_engine(config.DOMAIN_TREE_DATABASE_URL, echo=SQL_ECHO)


def get_session() -> Session:
    return Session(engine)

def get_scheduler_db_session() -> Session:
    return Session(get_scheduler_db_engine())

def get_domain_tree_session() -> Session:
    return Session(get_domain_tree_engine())
