#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from datetime import datetime
from rabbitmq_client import RabbitMQConsumer


def main():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "admin")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS", "123456")
    queue_name = os.getenv("RABBITMQ_QUEUE", "test_queue")

    producer = RabbitMQConsumer(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_user,
        password=rabbitmq_pass,
        queue_name=queue_name,
    )

    try:
        producer.connect()
        print(f"Connected to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")

        message_count = 1
        while True:
            message = {
                "message_id": message_count,
                "content": f"Test message {message_count}",
                "timestamp": datetime.now().isoformat(),
            }

            producer.publish_message(message)
            print(f"Sent message {message_count}")

            message_count += 1

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down producer...")
        producer.close()

    except Exception as e:
        print(f"Error: {str(e)}")
        producer.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
