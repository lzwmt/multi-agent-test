#!/usr/bin/env python3
"""
股票收盘报告 + 行业热点新闻
每天 15:30 发送
"""
import sys
import json
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace')
from realtime_data import RealtimeDataSource

# Discord 频道
DISCORD_CHANNEL = "1480762206458085376"

# 股票及行业分类
STOCKS = {
    '600104': {'name': '上汽集团', 'industry': '汽车'},
    '600150': {'name': '中国船舶', 'industry': '船舶制造'},
    '600326': {'name': '西藏天路', 'industry': '基建'},
    '600581': {'name': '八一钢铁', 'industry': '钢铁'},
    '603577': {'name': '汇金通', 'industry': '电力设备'},
    '600410': {'name': '华胜天成', 'industry': '科技'},
}

# 行业关键词映射
INDUSTRY_KEYWORDS = {
    '汽车': ['汽车', '新能源', '电动车', '比亚迪', '特斯拉', '造车新势力'],
    '船舶制造': ['船舶', '造船', '航运', '港口', '海运', '集装箱'],
    '基建': ['基建', '建筑', '房地产', '水泥', '工程机械', '一带一路'],
    '钢铁': ['钢铁', '铁矿石', '煤炭', '冶金', '建材'],
    '电力设备': ['电力', '电网', '新能源', '光伏', '风电', '储能'],
    '科技': ['科技', 'AI', '人工智能', '芯片', '半导体', '算力', '大模型'],
}

def get_stock_data():
    """获取股票今日数据"""
    data = {}
    for symbol, info in STOCKS.items():
        try:
            result, msg = RealtimeDataSource.tencent_realtime(symbol)
            if result:
                data[symbol] = {
                    'name': info['name'],
                    'industry': info['industry'],
                    'price': result['price'],
                    'change_pct': result['change_pct'],
                    'change_amount': result['change_amount'],
                    'open': result['open'],
                    'high': result['high'],
                    'low': result['low'],
                    'yesterday_close': result['yesterday_close'],
                    'volume': result['volume'],
                    'turnover': result['turnover'],
                }
        except Exception as e:
            print(f"获取 {symbol} 失败: {e}")
    return data

def get_industry_news(industry):
    """获取行业热点新闻（简化版，返回关键词）"""
    keywords = INDUSTRY_KEYWORDS.get(industry, [])
    return keywords[:3]  # 返回前3个关键词

def format_report(stock_data):
    """格式化收盘报告"""
    date_str = datetime.now().strftime("%Y年%m月%d日")
    
    lines = [
        f"📊 **股票收盘报告** - {date_str}",
        "",
        "🏆 **今日个股表现**",
        "",
    ]
    
    # 按涨跌幅排序
    sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    
    for symbol, data in sorted_stocks:
        emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
        lines.append(f"{emoji} **{data['name']}** ({symbol})")
        lines.append(f"   收盘价: ¥{data['price']:.2f}")
        lines.append(f"   涨跌: {data['change_pct']:+.2f}% ({data['change_amount']:+.2f})")
        lines.append(f"   最高: ¥{data['high']:.2f} | 最低: ¥{data['low']:.2f}")
        lines.append(f"   成交量: {data['volume']/10000:.1f}万手")
        lines.append(f"   成交额: ¥{data['turnover']/100000000:.2f}亿")
        
        # 行业热点
        keywords = get_industry_news(data['industry'])
        lines.append(f"   📰 行业: {data['industry']} | 热点: {', '.join(keywords)}")
        lines.append("")
    
    # 总结
    total_up = sum(1 for d in stock_data.values() if d['change_pct'] >= 0)
    total_down = len(stock_data) - total_up
    
    lines.append("📈 **今日总结**")
    lines.append(f"   上涨: {total_up}只 | 下跌: {total_down}只")
    lines.append(f"   最强: {sorted_stocks[0][1]['name']} (+{sorted_stocks[0][1]['change_pct']:.2f}%)")
    lines.append(f"   最弱: {sorted_stocks[-1][1]['name']} ({sorted_stocks[-1][1]['change_pct']:.2f}%)")
    lines.append("")
    lines.append("⏰ 数据时间: 收盘后")
    lines.append("💡 明日开盘: 9:30")
    
    return "\n".join(lines)

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成收盘报告...")
    
    stock_data = get_stock_data()
    if not stock_data:
        print("获取股票数据失败")
        return 1
    
    report = format_report(stock_data)
    
    print("\n" + "="*50)
    print("DISCORD_MESSAGE_START")
    print(json.dumps({
        "channel": "discord",
        "to": DISCORD_CHANNEL,
        "message": report
    }, ensure_ascii=False))
    print("DISCORD_MESSAGE_END")
    print("="*50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
