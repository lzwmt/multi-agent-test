#!/bin/bash
# 股票系统定时任务（资源优化版）
# 避免任务重叠，错峰执行

LOCK_FILE="/tmp/stock_cron.lock"

# 检查是否已有任务在运行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] 已有任务在运行(PID: $PID)，跳过"
        exit 0
    fi
fi

# 创建锁文件
echo $$ > "$LOCK_FILE"

cd /root/.openclaw/workspace

# 获取当前时间
HOUR=$(date +%H)
MINUTE=$(date +%M)
WEEKDAY=$(date +%u)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行定时任务"

# 1. 数据清理（每周日凌晨2点）
if [ "$WEEKDAY" -eq 7 ] && [ "$HOUR" -eq 2 ] && [ "$MINUTE" -eq 0 ]; then
    echo "执行数据清理..."
    python3 stock_data_cleanup.py >> /tmp/stock_cleanup.log 2>&1
fi

# 2. 盯盘监控（每5分钟，但只在交易时间）
if [ "$WEEKDAY" -le 5 ]; then
    if { [ "$HOUR" -eq 9 ] && [ "$MINUTE" -ge 30 ]; } || \
       [ "$HOUR" -eq 10 ] || \
       { [ "$HOUR" -eq 11 ] && [ "$MINUTE" -le 30 ]; } || \
       { [ "$HOUR" -ge 13 ] && [ "$HOUR" -lt 15 ]; }; then
        echo "执行盯盘监控..."
        timeout 60 python3 stock_monitor_local.py >> /tmp/stock_monitor.log 2>&1
    fi
fi

# 3. 数据更新（每小时，但只在交易时间）
if [ "$WEEKDAY" -le 5 ] && [ "$MINUTE" -eq 0 ]; then
    if { [ "$HOUR" -eq 9 ] && [ "$MINUTE" -ge 30 ]; } || \
       [ "$HOUR" -eq 10 ] || \
       { [ "$HOUR" -eq 11 ] && [ "$MINUTE" -le 30 ]; } || \
       { [ "$HOUR" -ge 13 ] && [ "$HOUR" -lt 15 ]; }; then
        echo "执行数据更新..."
        timeout 120 python3 stock_agent.py run >> /tmp/stock_agent.log 2>&1
    fi
fi

# 4. 收盘分析（15:35）
if [ "$HOUR" -eq 15 ] && [ "$MINUTE" -eq 35 ]; then
    echo "执行收盘分析..."
    timeout 180 python3 stock_analysis_v2.py >> /tmp/stock_analysis.log 2>&1
fi

# 删除锁文件
rm -f "$LOCK_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 定时任务完成"
