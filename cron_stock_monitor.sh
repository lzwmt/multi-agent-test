#!/bin/bash
# 股票盯盘系统定时任务脚本
# 使用方法:
# 1. 配置 Discord Webhook: export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
# 2. 添加到 crontab: crontab -e
#    */5 * * * * /root/.openclaw/workspace/cron_stock_monitor.sh

# 加载环境变量
if [ -f /root/.openclaw/workspace/.env ]; then
    source /root/.openclaw/workspace/.env
fi

cd /root/.openclaw/workspace

# 记录开始时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行盯盘任务" >> /tmp/stock_monitor.log

# 运行盯盘监控（单次）
python3 stock_monitor_local.py >> /tmp/stock_monitor.log 2>&1

# 每小时更新一次数据（交易时间）
HOUR=$(date +%H)
MINUTE=$(date +%M)
WEEKDAY=$(date +%u)

# 交易时间检查：周一至周五 9:30-11:30, 13:00-15:00
if [ "$WEEKDAY" -le 5 ]; then
    IS_TRADING=false
    
    # 上午 9:30-11:30
    if { [ "$HOUR" -eq 9 ] && [ "$MINUTE" -ge 30 ]; } || \
       [ "$HOUR" -eq 10 ] || \
       { [ "$HOUR" -eq 11 ] && [ "$MINUTE" -le 30 ]; }; then
        IS_TRADING=true
    fi
    
    # 下午 13:00-15:00
    if { [ "$HOUR" -ge 13 ] && [ "$HOUR" -lt 15 ]; } || \
       { [ "$HOUR" -eq 15 ] && [ "$MINUTE" -le 0 ]; }; then
        IS_TRADING=true
    fi
    
    if [ "$IS_TRADING" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 交易时间，更新数据..." >> /tmp/stock_monitor.log
        python3 stock_agent.py run >> /tmp/stock_agent.log 2>&1
    fi
fi

# 收盘后生成分析报告（15:30-15:40之间）
if [ "$HOUR" -eq 15 ] && [ "$MINUTE" -ge 30 ] && [ "$MINUTE" -le 40 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 收盘后分析..." >> /tmp/stock_monitor.log
    python3 stock_analysis_v2.py >> /tmp/stock_analysis.log 2>&1
    python3 stock_predictor_v2.py >> /tmp/stock_predictor.log 2>&1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 盯盘任务完成" >> /tmp/stock_monitor.log
