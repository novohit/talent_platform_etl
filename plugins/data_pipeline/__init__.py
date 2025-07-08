"""
数据管道插件包
提供完整的ETL数据处理管道功能
"""

__version__ = "2.0.0"
__author__ = "Talent Platform Team"

# 导出主要的接口
from .main import run_data_pipeline, DataPipeline

__all__ = [
    'run_data_pipeline',
    'DataPipeline'
] 