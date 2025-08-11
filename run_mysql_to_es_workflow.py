
# 工作流执行脚本: MySQL 到 Elasticsearch 同步

# 这个脚本硬编码并执行一个特定的任务链:
# 1. 执行 'mysql_test' 插件进行健康检查。
# 2. 如果成功，则执行 'es_indexer' 插件进行索引操作。


import logging
from celery import chain
from talent_platform.scheduler.tasks import execute_plugin_task, execute_chain_plugin_task

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """定义并启动工作流"""
    logger.info("准备启动 MySQL -> Elasticsearch 的链式工作流...")

    # 1. 定义任务链中的每一个步骤 (任务签名)
    
    # 步骤一: MySQL 健康检查
    mysql_task_signature = execute_plugin_task.s(
        plugin_name='mysql_test',
        operation='health_check'
    )
    
    # 步骤二: Elasticsearch 索引
    # 使用 .si() 创建一个不可变签名。
    # 这可以防止它接收前一个任务的返回值作为参数，从而解决 TypeError。
    es_task_signature = execute_chain_plugin_task.s(
        plugin_name='es_indexer',
    )

    # 2. 使用 chain() 将任务签名链接起来
    # 推荐使用逗号分隔，更清晰
    workflow_chain = chain(mysql_task_signature, es_task_signature)

    # 3. 异步执行工作流
    try:
        result = workflow_chain.apply_async()
        logger.info(f"工作流已成功启动。根任务 ID: {result.id}")
        
        print("\n✓ MySQL -> Elasticsearch 工作流已启动。")
        print(f"  根任务 ID: {result.id}")
        print("  请在 Celery Worker 的日志中查看执行详情。")

    except Exception as e:
        logger.error(f"启动工作流时发生错误: {e}")
        print(f"\n✗ 启动工作流失败: {e}")

if __name__ == "__main__":
    main()

