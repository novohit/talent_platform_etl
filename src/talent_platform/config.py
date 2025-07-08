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

    # Celery配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    # 插件系统配置
    PLUGINS_DIR = os.getenv("PLUGINS_DIR", "plugins")
    PLUGIN_VENV_DIR = os.getenv("PLUGIN_VENV_DIR", "plugin_envs")
    
    # 数据库变更监听配置
    DB_CHANGE_POLLING_INTERVAL = int(os.getenv("DB_CHANGE_POLLING_INTERVAL", "5"))  # 秒
    
    # 可继续添加其它配置项，并为每项设置合理默认值


config = Config()
