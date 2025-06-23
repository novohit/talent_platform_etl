import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/dbname")
    # 可继续添加其它配置项，并为每项设置合理默认值

config = Config() 