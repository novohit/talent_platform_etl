#!/bin/bash

# 调度系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查 Redis
    if ! command -v redis-server &> /dev/null; then
        print_error "Redis 未安装。请先安装 Redis。"
        exit 1
    fi
    
    # 检查 Redis 是否运行
    if ! redis-cli ping &> /dev/null; then
        print_warning "Redis 未运行，正在启动..."
        redis-server --daemonize yes
        sleep 2
        if redis-cli ping &> /dev/null; then
            print_success "Redis 启动成功"
        else
            print_error "Redis 启动失败"
            exit 1
        fi
    else
        print_success "Redis 已运行"
    fi
    
    # 检查 Python 包
    if ! python -c "import celery" &> /dev/null; then
        print_error "Celery 未安装。请运行: pip install celery redis"
        exit 1
    fi
    
    print_success "依赖检查完成"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p plugins
    mkdir -p plugin_envs
    mkdir -p cache
    
    print_success "目录创建完成"
}

# 检查环境配置
check_env() {
    print_info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，请创建并配置环境变量"
        cat << EOF > .env
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/talent_platform
DOMAIN_TREE_DATABASE_URL=mysql+pymysql://user:password@localhost:3306/domain_tree

# Elasticsearch 配置
ES_HOSTS=http://localhost:9200
ES_USERNAME=elastic
ES_PASSWORD=your_es_password
ES_TIMEOUT=30

# Redis 和 Celery 配置
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 插件系统配置
PLUGINS_DIR=plugins
PLUGIN_VENV_DIR=plugin_envs

# 数据库变更监听配置
DB_CHANGE_POLLING_INTERVAL=5
EOF
        print_info "已创建默认 .env 文件，请根据需要修改配置"
    fi
    
    print_success "环境配置检查完成"
}

# 启动服务
start_service() {
    local service=$1
    local options=$2
    
    case $service in
        "worker")
            print_info "启动 Celery Worker..."
            python -m talent_platform.scheduler_app worker $options &
            WORKER_PID=$!
            echo $WORKER_PID > .worker.pid
            print_success "Worker 已启动 (PID: $WORKER_PID)"
            ;;
        "beat")
            print_info "启动 Celery Beat..."
            python -m talent_platform.scheduler_app beat &
            BEAT_PID=$!
            echo $BEAT_PID > .beat.pid
            print_success "Beat 已启动 (PID: $BEAT_PID)"
            ;;
        "monitor")
            print_info "启动 Celery 监控..."
            python -m talent_platform.scheduler_app monitor &
            MONITOR_PID=$!
            echo $MONITOR_PID > .monitor.pid
            print_success "Monitor 已启动 (PID: $MONITOR_PID)"
            ;;
        *)
            print_error "未知服务: $service"
            exit 1
            ;;
    esac
}

# 停止服务
stop_service() {
    print_info "停止调度系统服务..."
    
    if [ -f ".worker.pid" ]; then
        kill $(cat .worker.pid) 2>/dev/null || true
        rm -f .worker.pid
        print_success "Worker 已停止"
    fi
    
    if [ -f ".beat.pid" ]; then
        kill $(cat .beat.pid) 2>/dev/null || true
        rm -f .beat.pid
        print_success "Beat 已停止"
    fi
    
    if [ -f ".monitor.pid" ]; then
        kill $(cat .monitor.pid) 2>/dev/null || true
        rm -f .monitor.pid
        print_success "Monitor 已停止"
    fi
}

# 显示状态
show_status() {
    print_info "调度系统状态:"
    
    echo "Services:"
    if [ -f ".worker.pid" ] && kill -0 $(cat .worker.pid) 2>/dev/null; then
        echo "  Worker: ✓ Running (PID: $(cat .worker.pid))"
    else
        echo "  Worker: ✗ Stopped"
    fi
    
    if [ -f ".beat.pid" ] && kill -0 $(cat .beat.pid) 2>/dev/null; then
        echo "  Beat: ✓ Running (PID: $(cat .beat.pid))"
    else
        echo "  Beat: ✗ Stopped"
    fi
    
    if [ -f ".monitor.pid" ] && kill -0 $(cat .monitor.pid) 2>/dev/null; then
        echo "  Monitor: ✓ Running (PID: $(cat .monitor.pid))"
    else
        echo "  Monitor: ✗ Stopped"
    fi
    
    echo ""
    echo "System Health:"
    python -m talent_platform.scheduler_app health
}

# 测试系统
test_system() {
    print_info "测试调度系统..."
    
    # 列出插件
    print_info "可用插件:"
    python -m talent_platform.scheduler_app list-plugins
    
    # 测试插件
    print_info "测试 data_processor 插件:"
    python -m talent_platform.scheduler_app test-plugin data_processor
    
    print_success "系统测试完成"
}

# 显示帮助信息
show_help() {
    echo "调度系统管理脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    显示系统状态"
    echo "  test      测试系统功能"
    echo "  worker    仅启动 Worker"
    echo "  beat      仅启动 Beat"
    echo "  monitor   仅启动监控"
    echo "  help      显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --queues QUEUES       指定队列 (worker 专用)"
    echo "  --concurrency N       指定并发数 (worker 专用)"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动所有服务"
    echo "  $0 worker --concurrency 4  # 启动 4 个并发的 Worker"
    echo "  $0 status                   # 显示状态"
}

# 主逻辑
main() {
    case "${1:-help}" in
        "start")
            check_dependencies
            create_directories
            check_env
            start_service "worker" "${@:2}"
            sleep 2
            start_service "beat"
            print_success "调度系统启动完成"
            print_info "使用 '$0 status' 检查状态"
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            stop_service
            sleep 2
            main start "${@:2}"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_system
            ;;
        "worker")
            check_dependencies
            create_directories
            check_env
            start_service "worker" "${@:2}"
            ;;
        "beat")
            check_dependencies
            create_directories
            check_env
            start_service "beat"
            ;;
        "monitor")
            check_dependencies
            create_directories
            check_env
            start_service "monitor"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 信号处理
trap 'print_info "正在停止服务..."; stop_service; exit 0' INT TERM

# 运行主逻辑
main "$@" 