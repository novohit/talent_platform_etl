import os
from dotenv import load_dotenv

# import socks
# import socket

# # 设置全局的 SOCKS5 代理
# socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7891)
# socket.socket = socks.socksocket

load_dotenv()


class Config:
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/dbname"
    )
    DOMAIN_TREE_DATABASE_URL = os.getenv(
        "DOMAIN_TREE_DATABASE_URL",
        "mysql+pymysql://user:password@localhost:3306/dbname",
    )
    # ES配置
    ES_HOSTS = os.getenv("ES_HOSTS", "http://localhost:9200").split(",")
    ES_USERNAME = os.getenv("ES_USERNAME", "elastic")
    ES_PASSWORD = os.getenv("ES_PASSWORD", "")
    ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))

    # 可继续添加其它配置项，并为每项设置合理默认值


config = Config()
