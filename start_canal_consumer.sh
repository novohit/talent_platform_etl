#!/bin/bash

# Canal消费者系统启动脚本

echo "🚇 Starting Canal Consumer System..."

# 设置默认环境变量
export CANAL_HOST=${CANAL_HOST:-"127.0.0.1"}
export CANAL_PORT=${CANAL_PORT:-"11111"}
export CANAL_DESTINATION=${CANAL_DESTINATION:-"example"}
export CANAL_BATCH_SIZE=${CANAL_BATCH_SIZE:-"100"}

echo "🔧 Configuration:"
echo "   Host: $CANAL_HOST"
echo "   Port: $CANAL_PORT"
echo "   Destination: $CANAL_DESTINATION"
echo "   Batch Size: $CANAL_BATCH_SIZE"

echo ""
echo "🚀 Starting Canal consumer..."

# 启动消费者
python -m talent_platform.consumers.consumer_app start \
    --host "$CANAL_HOST" \
    --port "$CANAL_PORT" \
    --destination "$CANAL_DESTINATION" \
    --batch-size "$CANAL_BATCH_SIZE" 