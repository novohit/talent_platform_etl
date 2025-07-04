from sqlmodel import create_engine, Session
from talent_platform.config import config
import socks
import socket

# 设置全局的 SOCKS5 代理
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7891)
socket.socket = socks.socksocket

engine = create_engine(config.DATABASE_URL, echo=True)


def get_domain_tree_engine():
    return create_engine(config.DOMAIN_TREE_DATABASE_URL, echo=True)


def get_session() -> Session:
    return Session(engine)


def get_domain_tree_session() -> Session:
    return Session(get_domain_tree_engine())
