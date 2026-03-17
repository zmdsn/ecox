#!/bin/bash
set -e

echo "=== 部署15分钟实时价格采集调度器 ==="

# 停止现有服务
echo "1. 停止现有服务..."
pkill -f "realtime.py" || echo "没有运行中的服务"

# 等待进程结束
sleep 2

# 启动新服务
echo "2. 启动新服务..."
mkdir -p logs
nohup uv run python -m ecox.data.realtime > logs/realtime.log 2>&1 &
echo $! > logs/realtime.pid

# 等待服务启动
sleep 3

# 验证服务运行
echo "3. 验证服务状态..."
if ps -p $(cat logs/realtime.pid) > /dev/null; then
    echo "✅ 服务启动成功 (PID: $(cat logs/realtime.pid))"
else
    echo "❌ 服务启动失败"
    exit 1
fi

# 显示日志
echo "4. 最近日志:"
tail -20 logs/realtime.log

echo ""
echo "=== 部署完成 ==="
echo "服务 PID: $(cat logs/realtime.pid)"
echo "日志文件: logs/realtime.log"
echo "监控命令: tail -f logs/realtime.log"
