#!/usr/bin/env python3
"""股票监控 - Discord 推送版（使用 Webhook）"""
import sys
import json
import urllib.request
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')
from realtime_data import RealtimeDataSource

# Discord Webhook URL
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1481133585619619890/llAm5tvRvkEinimejoKQr1g3etntjvC495rG262EOv7Nd48KMTg6zFsNVDhdlrPzdQvV"

STOCKS = {
    '600104': '上汽集团',
    '600150': '中国船舶',
    '600326': '西藏天路',
    '600581': '八一钢铁',
    '603577': '汇金通',
    '600410': '华胜天成',
}

def send_message(content):
    """发送 Discord 消息（使用 Webhook）"""
    try:
        data = json.dumps({"content": content}).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/1.0)"
        }
        req = urllib.request.Request(
            DISCORD_WEBHOOK,
            data=data,
            headers=headers,
            method='POST'
        )
        response = urllib.request.urlopen(req, timeout=10)
        return response.status == 204
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def get_quotes():
    """获取行情"""
    quotes = []
    for symbol, name in STOCKS.items():
        try:
            result, msg = RealtimeDataSource.tencent_realtime(symbol)
            if result:
                quotes.append({
                    'symbol': symbol,
                    'name': name,
                    'price': result['price'],
                    'change_pct': result['change_pct'],
                    'high': result['high'],
                    'low': result['low'],
                })
        except Exception as e:
            print(f"  {symbol} 错误: {e}")
    return quotes

def format_message(quotes):
    """格式化消息"""
    lines = ["📊 **股票盯盘监控**", f"⏰ {datetime.now().strftime('%H:%M:%S')}", ""]
    
    for q in quotes:
        emoji = "🟢" if q['change_pct'] >= 0 else "🔴"
        alert = " ⭐ 异动" if abs(q['change_pct']) >= 5 else ""
        lines.append(f"{emoji} **{q['name']}** ({q['symbol']}){alert}")
        lines.append(f"   价格: ¥{q['price']:.2f} | 涨跌: {q['change_pct']:+.2f}%")
        lines.append(f"   最高: ¥{q['high']:.2f} | 最低: ¥{q['low']:.2f}")
        lines.append("")
    
    lines.append(f"💡 数据源: 腾讯财经（实时）")
    return "\n".join(lines)

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始获取行情...")
    quotes = get_quotes()
    print(f"获取到 {len(quotes)} 只股票数据")
    
    if quotes:
        msg = format_message(quotes)
        print("\n发送消息到 Discord...")
        if send_message(msg):
            print("✅ 已发送")
        else:
            print("❌ 发送失败，尝试备用方式...")
            # 备用：输出消息供手动发送
            print("\n消息内容:")
            print(msg)
    else:
        print("获取失败")
