#!/usr/bin/env python3
"""
股票收盘报告 V3 - 大模型预测版
生成提示词，由主程序调用大模型分析
"""
import sys
import json
import sqlite3
import os
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')
from realtime_data import RealtimeDataSource

# 股票及行业分类
STOCKS = {
    '600104': {'name': '上汽集团', 'industry': '汽车', 'industry_key': '新能源汽车产业链'},
    '600150': {'name': '中国船舶', 'industry': '船舶制造', 'industry_key': '船舶与海洋工程'},
    '600326': {'name': '西藏天路', 'industry': '基建', 'industry_key': '基建与建材'},
    '600581': {'name': '八一钢铁', 'industry': '钢铁', 'industry_key': '钢铁与冶金'},
    '603577': {'name': '汇金通', 'industry': '电力设备', 'industry_key': '电力与新能源'},
    '600410': {'name': '华胜天成', 'industry': '科技', 'industry_key': '科技与数字化'},
}

TRENDRADAR_DB_PATH = '/root/.openclaw/workspace/TrendRadar/output/news'

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
                    'industry_key': info['industry_key'],
                    'price': result['price'],
                    'change_pct': result['change_pct'],
                    'change_amount': result['change_amount'],
                    'open': result['open'],
                    'high': result['high'],
                    'low': result['low'],
                    'volume': result['volume'],
                    'turnover': result['turnover'],
                }
        except Exception as e:
            print(f"获取 {symbol} 失败: {e}", file=sys.stderr)
    return data

def get_industry_news():
    """从 TrendRadar 获取行业新闻"""
    news_by_industry = {}
    today = datetime.now().strftime('%Y-%m-%d')
    db_path = os.path.join(TRENDRADAR_DB_PATH, f'{today}.db')
    
    if not os.path.exists(db_path):
        return news_by_industry
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        industry_keywords = {
            '新能源汽车产业链': ['新能源汽车', '电动车', '锂电池', '充电桩', '汽车销量', '智能驾驶', '比亚迪', '蔚来', '小鹏', '理想', '特斯拉'],
            '船舶与海洋工程': ['船舶', '造船', '航母', '军舰', '舰艇', '海军', '海工装备', '航运', '港口'],
            '基建与建材': ['水泥', '建材', '基建', '房地产', '西部大开发', '一带一路', '西藏'],
            '钢铁与冶金': ['钢铁', '钢材', '铁矿石', '焦炭', '新疆'],
            '电力与新能源': ['特高压', '电网', '储能', '光伏', '风电', '核电', '新能源'],
            '科技与数字化': ['云计算', 'AI', '人工智能', '大数据', '算力', '信创', '数据中心']
        }
        
        cursor.execute('SELECT title, platform_id, rank FROM news_items')
        rows = cursor.fetchall()
        
        for title, platform, rank in rows:
            for industry, kws in industry_keywords.items():
                for kw in kws:
                    if kw in title:
                        if industry not in news_by_industry:
                            news_by_industry[industry] = []
                        if not any(n['title'] == title for n in news_by_industry[industry]):
                            news_by_industry[industry].append({
                                'title': title, 'platform': platform, 'rank': rank
                            })
                        break
        
        conn.close()
    except Exception as e:
        print(f"读取新闻失败: {e}", file=sys.stderr)
    
    return news_by_industry

def generate_analysis_prompt(symbol, data, industry_news):
    """生成大模型分析提示词"""
    industry_key = data['industry_key']
    related_news = industry_news.get(industry_key, [])
    
    news_text = ""
    if related_news:
        news_text = "\n【相关行业新闻】\n"
        for i, news in enumerate(related_news[:3], 1):
            news_text += f"{i}. [{news['platform']}] {news['title']}\n"
    
    prompt = f"""分析股票 {data['name']}({symbol}) 并预测明日走势。

【股票数据】
- 行业: {data['industry']}
- 收盘价: ¥{data['price']:.2f}
- 今日涨跌: {data['change_pct']:+.2f}%
- 今日振幅: {((data['high'] - data['low']) / data['price'] * 100):.2f}%
- 成交量: {data['volume']/10000:.1f}万手
- 成交额: ¥{data['turnover']/10000:.2f}亿
{news_text}
【分析要求】
1. 技术面: 分析今日走势特征、关键价位
2. 资金面: 分析成交量变化
3. 消息面: 评估行业新闻影响
4. 预测: 明日走势方向、幅度、目标价、置信度

【回复格式】
方向: 上涨/下跌/震荡
幅度: +/-X.XX%
目标价: ¥XX.XX
置信度: XX%
分析: 简要技术面分析（1句）
理由: 综合判断理由（2-3句）"""
    
    return prompt

def main():
    """主函数：生成数据和大模型提示词"""
    stock_data = get_stock_data()
    if not stock_data:
        print(json.dumps({"error": "获取股票数据失败"}))
        return 1
    
    industry_news = get_industry_news()
    
    # 生成每个股票的分析提示词
    analysis_tasks = []
    for symbol, data in stock_data.items():
        prompt = generate_analysis_prompt(symbol, data, industry_news)
        analysis_tasks.append({
            "symbol": symbol,
            "name": data['name'],
            "data": data,
            "prompt": prompt
        })
    
    # 输出 JSON 格式，供主程序调用大模型
    output = {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "stocks": stock_data,
        "industry_news": industry_news,
        "analysis_tasks": analysis_tasks
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
