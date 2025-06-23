from sqlmodel import create_engine, Session
from config import config

engine = create_engine(config.DATABASE_URL, echo=True)


def get_session():
    return Session(engine)
