#!/bin/bash
# 股票信息自动推送脚本
# 推送到 Discord 频道 1480762206458085376

cd /root/.openclaw/workspace

CHANNEL="1480762206458085376"

# 检查当前时间
HOUR=$(date +%H)
MINUTE=$(date +%M)

# 交易时间判断
if [ "$HOUR" -ge 9 ] && [ "$HOUR" -le 15 ]; then
    IS_TRADING="交易时间"
else
    IS_TRADING="非交易时间"
fi

# 生成盯盘报告
python3 stock_monitor_local.py > /tmp/monitor_report.txt 2>&1

# 提取关键信息
ALERTS=$(grep "告警触发" /tmp/monitor_report.txt | head -1)
if echo "$ALERTS" | grep -q "告警触发"; then
    # 有告警，发送通知
    python3 -c "
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from stock_monitor_local import LocalStockMonitor
monitor = LocalStockMonitor()
prices = monitor.get_latest_prices()
alerts = monitor.check_alerts(prices)
for alert in alerts:
    print(alert['message'])
" > /tmp/alerts.txt
    
    # 发送告警到 Discord
    if [ -s /tmp/alerts.txt ]; then
        ALERT_MSG=$(cat /tmp/alerts.txt)
        /usr/local/bin/openclaw message send --target "$CHANNEL" --text "🚨 **股票告警** ($IS_TRADING)\n\n$ALERT_MSG" 2>/dev/null || echo "告警: $ALERT_MSG"
    fi
fi

# 收盘后发送完整报告 (15:35)
if [ "$HOUR" -eq 15 ] && [ "$MINUTE" -eq 35 ]; then
    # 生成分析报告
    python3 stock_analysis_v2.py > /tmp/analysis_report.txt 2>&1
    python3 stock_predictor_v2.py > /tmp/predictor_report.txt 2>&1
    
    # 发送收盘总结
    /usr/local/bin/openclaw message send --target "$CHANNEL" --text "📊 **收盘分析报告已生成**\n请查看完整报告" 2>/dev/null || echo "收盘报告已生成"
fi

# 每小时发送一次状态摘要
if [ "$MINUTE" -eq 0 ]; then
    # 生成简要状态
    python3 -c "
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/stock_data.db'
conn = sqlite3.connect(DB_PATH)

# 获取最新价格
df = pd.read_sql_query('''
    SELECT symbol, close, change_pct
    FROM stock_prices
    WHERE date = (SELECT MAX(date) FROM stock_prices)
    AND symbol IN ('600104', '600150', '600326', '600581', '603577', '600410')
''', conn)

conn.close()

if not df.empty:
    print('📈 **股票状态更新** (' + datetime.now().strftime('%H:%M') + ')\n')
    for _, row in df.iterrows():
        emoji = '📈' if row['change_pct'] > 0 else '📉'
        print(f\"{emoji} {row['symbol']}: ¥{row['close']:.2f} ({row['change_pct']:+.2f}%)\")
" > /tmp/hourly_status.txt
    
    STATUS_MSG=$(cat /tmp/hourly_status.txt)
    /usr/local/bin/openclaw message send --target "$CHANNEL" --text "$STATUS_MSG" 2>/dev/null || echo "$STATUS_MSG"
fi
