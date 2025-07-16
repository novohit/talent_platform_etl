#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pika
import json
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        queue_name: str = "test_queue",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def connect(self) -> None:
        """建立到RabbitMQ的连接"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)

            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            self.channel.queue_declare(queue=self.queue_name, durable=True)

            logger.info(
                f"Successfully connected to RabbitMQ and declared queue: {self.queue_name}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def setup_dlx(
        self, dlx_exchange: str, dlx_queue: str, ttl: int | None = None
    ) -> None:
        """设置死信交换机和队列

        Args:
            dlx_exchange: 死信交换机名称
            dlx_queue: 死信队列名称
            ttl: 消息过期时间（毫秒），可选
        """
        try:
            if self.channel is None:
                raise RuntimeError(
                    "Channel is not established. Please call connect() first."
                )

            # 声明死信交换机
            self.channel.exchange_declare(
                exchange=dlx_exchange, exchange_type="direct", durable=True
            )

            # 声明死信队列
            self.channel.queue_declare(queue=dlx_queue, durable=True)

            # 绑定死信队列到死信交换机
            self.channel.queue_bind(
                queue=dlx_queue,
                exchange=dlx_exchange,
                routing_key=self.queue_name,  # 使用原队列名作为路由键
            )

            # 为原队列添加死信配置
            arguments = {
                "x-dead-letter-exchange": dlx_exchange,
                "x-dead-letter-routing-key": self.queue_name,
            }

            # 如果设置了TTL，添加到参数中
            if ttl is not None:
                arguments["x-message-ttl"] = str(ttl)  # RabbitMQ需要字符串形式的值

            # 重新声明原队列，添加死信配置
            self.channel.queue_declare(
                queue=self.queue_name, durable=True, arguments=arguments
            )

            logger.info(
                f"Successfully setup DLX: {dlx_exchange} with queue: {dlx_queue}"
            )

        except Exception as e:
            logger.error(f"Failed to setup DLX: {str(e)}")
            raise

    def start_consuming(self, callback, prefetch_count: int = 1) -> None:
        """开始消费消息

        Args:
            callback: 处理消息的回调函数，格式为 callback(ch, method, properties, body)
                     ch: pika.Channel
                     method: pika.spec.Basic.Deliver
                     properties: pika.spec.BasicProperties
                     body: bytes
            prefetch_count: 预取消息数量，默认为1
        """
        try:
            if self.channel is None:
                raise RuntimeError(
                    "Channel is not established. Please call connect() first."
                )

            # 每次只处理一条消息 可以调整 参数传入
            self.channel.basic_qos(prefetch_count=prefetch_count)

            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=callback
            )

            logger.info(f"Started consuming from queue: {self.queue_name}")
            logger.info("Waiting for messages. To exit press CTRL+C")

            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.close()

        except Exception as e:
            logger.error(f"Error while consuming messages: {str(e)}")
            self.close()

    def publish_message(
        self,
        message: Dict[str, Any],
        exchange: str = "",
        routing_key: str | None = None,
    ) -> None:
        """发送消息到RabbitMQ

        Args:
            message: 要发送的消息内容（字典格式，将被转换为JSON）
            exchange: 交换机名称，默认使用默认交换机
            routing_key: 路由键，如果未指定则使用初始化时的queue_name
        """
        try:
            if self.channel is None:
                raise RuntimeError(
                    "Channel is not established. Please call connect() first."
                )

            # 如果未指定routing_key，使用默认的queue_name
            if routing_key is None:
                routing_key = self.queue_name

            message_body = json.dumps(message, ensure_ascii=False).encode("utf-8")

            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                    content_type="application/json",
                ),
            )

            logger.info(
                f"Successfully published message to exchange: {exchange}, routing_key: {routing_key}"
            )

        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            raise

    def close(self) -> None:
        """关闭连接"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            logger.info("Successfully closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")
