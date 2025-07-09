from sqlmodel import Session, create_engine

from talent_platform.config import config


engine = create_engine(config.DATABASE_URL, echo=True)

def get_scheduler_db_engine():
    return create_engine(config.DOMAIN_TREE_DATABASE_URL, echo=True)

def get_domain_tree_engine():
    return create_engine(config.DOMAIN_TREE_DATABASE_URL, echo=True)


def get_session() -> Session:
    return Session(engine)

def get_scheduler_db_session() -> Session:
    return Session(get_scheduler_db_engine())

def get_domain_tree_session() -> Session:
    return Session(get_domain_tree_engine())
