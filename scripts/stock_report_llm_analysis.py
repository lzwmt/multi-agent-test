#!/usr/bin/env python3
"""
使用大模型分析单只股票
被 stock_closing_report_llm.py 调用
"""
import sys
import json

def analyze_stock(stock_json):
    """分析股票并返回预测结果"""
    data = json.loads(stock_json)
    
    symbol = data['symbol']
    name = data['name']
    industry = data['industry']
    price = data['price']
    change_pct = data['change_pct']
    volume = data['volume']
    turnover = data['turnover']
    news = data.get('news', [])
    
    # 构建提示词
    news_text = ""
    if news:
        news_text = "\n相关行业新闻:\n"
        for i, n in enumerate(news[:3], 1):
            news_text += f"{i}. [{n['platform']}] {n['title']}\n"
    
    prompt = f"""作为专业股票分析师，分析以下股票并预测明日走势。

股票: {name} ({symbol})
行业: {industry}
当前价格: ¥{price:.2f}
今日涨跌: {change_pct:+.2f}%
成交量: {volume/10000:.1f}万手
成交额: ¥{turnover/10000:.2f}亿
{news_text}

请分析:
1. 技术面（趋势、支撑压力）
2. 资金面（成交量变化）
3. 消息面（行业新闻影响）
4. 预测明日走势（方向+幅度+目标价+置信度）

回复格式:
方向: 上涨/下跌/震荡
预测幅度: +/-X.XX%
目标价: ¥XX.XX
置信度: XX%
理由: 简要说明（2-3句）"""
    
    return prompt

if __name__ == "__main__":
    if len(sys.argv) > 1:
        stock_data = sys.argv[1]
        result = analyze_stock(stock_data)
        print(result)
