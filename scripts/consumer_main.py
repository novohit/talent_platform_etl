#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from rabbitmq_client import RabbitMQConsumer

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_message(ch, method, properties, body: bytes) -> None:
    """自定义的消息处理函数

    Args:
        ch: pika.Channel
        method: pika.spec.Basic.Deliver
        properties: pika.spec.BasicProperties
        body: bytes
    """
    try:
        message = json.loads(body.decode())
        logger.info(f"Received message: {message}")

        # 模拟消息处理
        # 如果消息ID是3的倍数，我们拒绝这个消息
        if message.get("message_id", 0) % 3 == 0:
            logger.warning(
                f"Rejecting message {message.get('message_id')} (will be sent to DLX)"
            )
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return

        # TODO: 处理业务调用 run_worker

        # 处理成功，手动确认消息
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        logger.warning(f"Received non-JSON message: {body.decode()}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # 处理失败，拒绝消息并重新入队
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def process_dlx_message(ch, method, properties, body: bytes) -> None:
    """处理死信队列中的消息

    Args:
        ch: pika.Channel
        method: pika.spec.Basic.Deliver
        properties: pika.spec.BasicProperties
        body: bytes
    """
    try:
        message = json.loads(body.decode())
        logger.warning(f"Received message in DLX: {message}")

        # 这里可以添加特殊的处理逻辑，比如：
        # - 记录到错误日志
        # - 发送告警
        # - 存储到特殊的数据库表

        # 确认死信消息
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing DLX message: {str(e)}")
        # 在死信队列中的消息处理失败，直接确认（防止无限循环）
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "admin")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS", "123456")
    queue_name = os.getenv("RABBITMQ_QUEUE", "test_queue")

    # 创建主队列消费者
    consumer = RabbitMQConsumer(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_user,
        password=rabbitmq_pass,
        queue_name=queue_name,
    )

    # 创建死信队列消费者
    dlx_consumer = RabbitMQConsumer(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_user,
        password=rabbitmq_pass,
        queue_name=f"{queue_name}_dlx",  # 死信队列名称
    )

    try:
        # 连接并设置死信交换机
        consumer.connect()
        consumer.setup_dlx(
            dlx_exchange=f"{queue_name}_dlx",
            dlx_queue=f"{queue_name}_dlx",
            ttl=1800000,  # 30分钟过期时间
        )

        # 连接死信队列消费者
        dlx_consumer.connect()

        logger.info(f"Connected to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
        logger.info(f"Consuming messages from queue: {queue_name}")
        logger.info(f"Dead letters will be routed to: {queue_name}_dlx")
        logger.info("Press CTRL+C to exit")

        # 启动死信队列消费者（在新进程中）
        import multiprocessing

        dlx_process = multiprocessing.Process(
            target=dlx_consumer.start_consuming, args=(process_dlx_message,)
        )
        dlx_process.start()

        # 启动主队列消费者
        consumer.start_consuming(callback=process_message)

    except KeyboardInterrupt:
        logger.info("\nShutting down consumer...")
        consumer.close()
        dlx_consumer.close()
        if "dlx_process" in locals():
            dlx_process.terminate()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        consumer.close()
        dlx_consumer.close()
        if "dlx_process" in locals():
            dlx_process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    main()
