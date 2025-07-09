#!/usr/bin/env python3
"""
创建调度任务数据库表
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlmodel import SQLModel, create_engine
from talent_platform.config import config
from talent_platform.db.models import ScheduledTaskModel
from talent_platform.logger import logger
from talent_platform.db.database import get_domain_tree_engine

def create_tables():
    """创建数据库表"""
    try:
        # 创建数据库引擎
        engine = get_domain_tree_engine()
        
        # 创建所有表
        SQLModel.metadata.create_all(engine)
        
        logger.info("✅ Database tables created successfully!")
        logger.info(f"Created table: {ScheduledTaskModel.__tablename__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False

def main():
    """主函数"""
    print("🗄️ Creating database tables for scheduled tasks...")
    
    success = create_tables()
    
    if success:
        print("✅ Database initialization completed!")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 