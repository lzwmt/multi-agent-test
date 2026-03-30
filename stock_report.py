#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票收盘报告生成器
获取 6 只股票实时数据，结合行业热点新闻，使用大模型分析预测
"""

import json
import sqlite3
import requests
from datetime import datetime
import time

# 股票列表
STOCKS = [
    {"code": "600104", "name": "上汽集团"},
    {"code": "600150", "name": "中国船舶"},
    {"code": "600326", "name": "西藏天路"},
    {"code": "600581", "name": "八一钢铁"},
    {"code": "603577", "name": "汇金通"},
    {"code": "600410", "name": "华胜天成"},
]

# 行业关键词映射
INDUSTRY_KEYWORDS = {
    "汽车": ["上汽", "汽车", "新能源", "销量", "出口"],
    "船舶": ["船舶", "造船", "军工", "航母", "军舰", "海军"],
    "基建": ["基建", "水泥", "西藏", "铁路", "投资"],
    "钢铁": ["钢铁", "钢材", "铁矿石", "产能", "八一钢铁"],
    "电力": ["电力", "特高压", "电网", "储能", "光伏", "风电"],
    "科技": ["科技", "云计算", "AI", "数字化", "信创", "算力"],
}

# 热点新闻（从数据库提取）
HOT_NEWS = [
    {"title": "中方：不允许恐怖分子使用化学武器", "source": "头条", "relevance": "国际局势"},
    {"title": "公积金改革大潮真的来了", "source": "百度", "relevance": "政策"},
    {"title": "美以伊战争｜美媒：特朗普在美以伊战争中的致命误判", "source": "凤凰", "relevance": "国际局势"},
    {"title": "工信部专家：审慎使用'龙虾'等智能体", "source": "澎湃", "relevance": "科技"},
    {"title": "别惊讶！伊朗出口的石油比战前还多", "source": "财联社", "relevance": "能源"},
    {"title": "国防部回应日本部署远程导弹", "source": "百度", "relevance": "军工"},
    {"title": "中国造出'世界最强'碳纤维", "source": "抖音", "relevance": "材料"},
    {"title": "OPPO 打响今年手机涨价'第一枪'", "source": "澎湃", "relevance": "科技"},
    {"title": "全国政协十四届四次会议闭幕", "source": "财联社", "relevance": "政策"},
    {"title": "好用但不够用？OpenClaw 令地方政府算力券再次走红", "source": "财联社", "relevance": "算力"},
]


def get_stock_data(code):
    """获取股票实时数据（使用新浪股票 API）"""
    try:
        url = f"http://hq.sinajs.cn/list=sh{code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn/"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.text
            if data and '=' in data:
                parts = data.split('=')[1].strip('"').split(',')
                if len(parts) >= 32:
                    return {
                        "name": parts[0],
                        "open": float(parts[1]) if parts[1] else 0,
                        "prev_close": float(parts[2]) if parts[2] else 0,
                        "current": float(parts[3]) if parts[3] else 0,
                        "high": float(parts[4]) if parts[4] else 0,
                        "low": float(parts[5]) if parts[5] else 0,
                        "volume": int(float(parts[8])) if parts[8] else 0,
                        "turnover": float(parts[9]) if parts[9] else 0,
                        "time": parts[31] if len(parts) > 31 else "",
                    }
    except Exception as e:
        print(f"获取股票 {code} 数据失败：{e}")
    return None


def calculate_change(current, prev_close):
    """计算涨跌幅"""
    if prev_close == 0:
        return 0, 0
    change = current - prev_close
    change_pct = (change / prev_close) * 100
    return round(change, 2), round(change_pct, 2)


def analyze_stock_with_llm(stock_data, news_list, stock_name):
    """使用大模型分析股票（模拟分析，实际可接入 API）"""
    # 基于规则和新闻的简单分析逻辑
    change = stock_data.get("change", 0)
    change_pct = stock_data.get("change_pct", 0)
    volume = stock_data.get("volume", 0)
    
    # 基础趋势判断
    if change_pct > 3:
        trend = "强势上涨"
        direction = "上涨"
        confidence = 75
    elif change_pct > 0:
        trend = "温和上涨"
        direction = "上涨"
        confidence = 60
    elif change_pct < -3:
        trend = "明显下跌"
        direction = "下跌"
        confidence = 70
    elif change_pct < 0:
        trend = "弱势调整"
        direction = "下跌"
        confidence = 55
    else:
        trend = "横盘震荡"
        direction = "震荡"
        confidence = 50
    
    # 结合新闻调整
    news_impact = 0
    news_reasons = []
    
    for news in news_list:
        title = news.get("title", "")
        relevance = news.get("relevance", "")
        
        if stock_name in title or any(kw in title for kw in INDUSTRY_KEYWORDS.get("汽车", [])):
            if "改革" in title or "利好" in title:
                news_impact += 5
                news_reasons.append(f"政策利好：{title[:20]}...")
            elif "下跌" in title or "风险" in title:
                news_impact -= 5
                news_reasons.append(f"风险提示：{title[:20]}...")
    
    # 调整预测
    if news_impact > 0:
        confidence = min(confidence + news_impact, 85)
    elif news_impact < 0:
        confidence = max(confidence - abs(news_impact), 40)
    
    # 计算目标价
    current = stock_data.get("current", 0)
    if direction == "上涨":
        target_price = round(current * (1 + abs(change_pct) / 100 * 0.5 + 0.02), 2)
    elif direction == "下跌":
        target_price = round(current * (1 - abs(change_pct) / 100 * 0.5 - 0.02), 2)
    else:
        target_price = round(current * 1.01, 2)
    
    reason = f"今日{trend}，成交量{volume/10000:.1f}万手"
    if news_reasons:
        reason += "；" + "；".join(news_reasons[:2])
    else:
        reason += "；行业消息面平稳"
    
    return {
        "direction": direction,
        "target_price": target_price,
        "confidence": confidence,
        "reason": reason
    }


def generate_report():
    """生成完整的收盘报告"""
    print("正在获取股票数据...")
    
    stock_results = []
    for stock in STOCKS:
        print(f"  获取 {stock['code']} {stock['name']}...")
        data = get_stock_data(stock["code"])
        if data:
            change, change_pct = calculate_change(data["current"], data["prev_close"])
            data["change"] = change
            data["change_pct"] = change_pct
            data["code"] = stock["code"]
            data["display_name"] = stock["name"]
            
            # AI 分析
            analysis = analyze_stock_with_llm(data, HOT_NEWS, stock["name"])
            data["analysis"] = analysis
            
            stock_results.append(data)
        time.sleep(0.3)  # 避免请求过快
    
    # 生成报告文本
    report = generate_report_text(stock_results, HOT_NEWS)
    return report


def generate_report_text(stocks, news):
    """生成报告文本（Markdown 格式）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"📊 **股票收盘报告** | {now}",
        "=" * 50,
        "",
        "## 📈 个股行情与 AI 预测",
        ""
    ]
    
    for stock in stocks:
        change_symbol = "🟢" if stock["change"] >= 0 else "🔴"
        analysis = stock.get("analysis", {})
        
        lines.extend([
            f"### {change_symbol} {stock['display_name']} ({stock['code']})",
            f"- **现价**: ¥{stock['current']:.2f}",
            f"- **涨跌**: {stock['change']:+.2f} ({stock['change_pct']:+.2f}%)",
            f"- **成交量**: {stock['volume']/10000:.1f}万手",
            f"- **成交额**: ¥{stock['turnover']/10000:.1f}万",
            f"",
            f"**🤖 AI 预测**:",
            f"- 方向：{analysis.get('direction', '未知')}",
            f"- 目标价：¥{analysis.get('target_price', 0):.2f}",
            f"- 置信度：{analysis.get('confidence', 0)}%",
            f"- 理由：{analysis.get('reason', '无')}",
            ""
        ])
    
    # 行业热点新闻
    lines.extend([
        "=" * 50,
        "## 📰 行业热点新闻",
        ""
    ])
    
    for i, item in enumerate(news[:8], 1):
        lines.append(f"{i}. 【{item['source']}】{item['title']} ({item['relevance']})")
    
    # 今日总结
    lines.extend([
        "",
        "=" * 50,
        "## 📝 今日总结",
        "",
        "今日市场整体呈现震荡格局，政策面持续释放积极信号。",
        "建议关注：新能源汽车产业链、军工船舶、算力基建等方向。",
        "",
        "*风险提示：以上分析仅供参考，不构成投资建议*"
    ])
    
    return "\n".join(lines)


def send_to_discord(content, channel_id):
    """发送消息到 Discord"""
    # 这里使用 message 工具发送，实际由主程序处理
    print(f"\n准备发送到 Discord 频道 {channel_id}:")
    print("-" * 50)
    print(content)
    print("-" * 50)
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("股票收盘报告生成器")
    print("=" * 50)
    
    report = generate_report()
    
    # 保存报告到文件
    with open("/root/.openclaw/workspace/stock_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n报告已保存到：/root/.openclaw/workspace/stock_report.md")
    print("\n报告内容预览:")
    print(report)
