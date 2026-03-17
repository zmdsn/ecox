#!/bin/bash
echo "=== 实时价格调度器监控 ==="
echo ""

# 检查进程状态
echo "📌 进程状态:"
if [ -f logs/realtime.pid ]; then
    PID=$(cat logs/realtime.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "   ✅ 服务运行中 (PID: $PID)"
        echo "   运行时间: $(ps -p $PID -o etime= | tr -d ' ')"
    else
        echo "   ❌ 服务未运行 (PID文件存在但进程不存在)"
        exit 1
    fi
else
    echo "   ❌ 服务未运行 (无PID文件)"
    exit 1
fi

echo ""

# 显示最近触发时间
echo "🕐 最近触发时间:"
grep "定时触发抓取" logs/realtime.log | tail -5 | while read line; do
    echo "   $line"
done

echo ""

# 显示采集统计
echo "📊 今日采集统计:"
START_OF_DAY=$(date +%Y-%m-%d)
grep "$START_OF_DAY" logs/realtime.log | grep "保存完成" | tail -1 || echo "   暂无今日数据"

echo ""

# 显示错误（如果有）
echo "⚠️  最近错误:"
grep "ERROR" logs/realtime.log | tail -3 || echo "   无错误"

echo ""
echo "=== 监控完成 ==="
echo "实时日志: tail -f logs/realtime.log"
