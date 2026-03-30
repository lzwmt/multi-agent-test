#!/usr/bin/env python3
"""
大模型股票分析
使用阿里云百炼API进行新闻情绪分析和综合投资建议
"""

import sqlite3
import pandas as pd
import json
import requests
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/stock_data.db"
API_KEY = "sk-sp-464beb4134c346e7bfedde1f78049feb"
API_BASE = "https://coding.dashscope.aliyuncs.com/v1"

STOCKS = {
    '600104': '上汽集团',
    '600150': '中国船舶',
    '600326': '西藏天路',
    '600581': '八一钢铁',
    '603577': '汇金通',
}

def init_llm_tables():
    """初始化大模型分析表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 大模型分析报告表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            analysis_type TEXT,
            content TEXT,
            sentiment TEXT,
            recommendation TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("大模型分析表初始化完成")

def call_llm(prompt, model="qwen-max"):
    """调用大模型API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一位专业的股票分析师，擅长技术分析和基本面分析。请给出简洁、专业的分析。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

def get_stock_data(symbol):
    """获取股票数据"""
    conn = sqlite3.connect(DB_PATH)
    
    # 最新价格和指标
    price_df = pd.read_sql_query('''
        SELECT * FROM stock_indicators 
        WHERE symbol = ? 
        ORDER BY date DESC LIMIT 5
    ''', conn, params=(symbol,))
    
    # 预测结果
    pred_df = pd.read_sql_query('''
        SELECT * FROM price_predictions 
        WHERE symbol = ? 
        ORDER BY created_at DESC LIMIT 1
    ''', conn, params=(symbol,))
    
    # 交易信号
    signal_df = pd.read_sql_query('''
        SELECT * FROM trading_signals 
        WHERE symbol = ? 
        ORDER BY date DESC LIMIT 3
    ''', conn, params=(symbol,))
    
    conn.close()
    
    return price_df, pred_df, signal_df

def analyze_technical(symbol):
    """技术分析"""
    price_df, pred_df, signal_df = get_stock_data(symbol)
    
    if price_df.empty:
        return None
    
    latest = price_df.iloc[0]
    name = STOCKS.get(symbol, symbol)
    
    prompt = f"""请对{name}({symbol})进行技术分析：

当前数据：
- 收盘价: {latest['close']:.2f}
- MA5: {latest['ma5']:.2f}
- MA10: {latest['ma10']:.2f}
- MA20: {latest['ma20']:.2f}
- RSI6: {latest['rsi6']:.1f}
- MACD柱状: {latest['macd_bar']:.4f}
- 波动率: {latest['volatility']:.2f}%

请给出：
1. 趋势判断（上涨/下跌/震荡）
2. 关键支撑位和压力位
3. 操作建议（买入/持有/卖出）
4. 风险等级（低/中/高）

请用简洁的中文回答，控制在200字以内。"""
    
    return call_llm(prompt)

def analyze_prediction(symbol):
    """预测分析"""
    price_df, pred_df, signal_df = get_stock_data(symbol)
    
    if pred_df.empty or price_df.empty:
        return None
    
    latest_price = price_df.iloc[0]
    latest_pred = pred_df.iloc[0]
    name = STOCKS.get(symbol, symbol)
    
    prompt = f"""请分析{name}({symbol})的AI预测结果：

当前价格: {latest_price['close']:.2f}
AI预测明日价格: {latest_pred['predicted_close']:.2f}
预测涨跌: {((latest_pred['predicted_close'] - latest_price['close']) / latest_price['close'] * 100):+.2f}%
预测置信度: {latest_pred['confidence']*100:.1f}%

技术指标：
- RSI: {latest_price['rsi6']:.1f}（{'超买' if latest_price['rsi6'] > 70 else '超卖' if latest_price['rsi6'] < 30 else '正常'}）
- MACD: {'金叉' if latest_price['macd_bar'] > 0 else '死叉'}

请综合以上信息给出投资建议，控制在150字以内。"""
    
    return call_llm(prompt)

def analyze_portfolio():
    """组合分析"""
    conn = sqlite3.connect(DB_PATH)
    
    # 获取所有股票最新数据
    df = pd.read_sql_query('''
        SELECT i.symbol, i.close, i.rsi6, i.ma5, i.ma10, i.ma20,
               p.predicted_close, p.confidence
        FROM stock_indicators i
        LEFT JOIN price_predictions p ON i.symbol = p.symbol
        WHERE i.date = (SELECT MAX(date) FROM stock_indicators)
        AND (p.prediction_date = (SELECT MAX(prediction_date) FROM price_predictions) OR p.prediction_date IS NULL)
    ''', conn)
    
    conn.close()
    
    # 构建组合描述
    stocks_desc = []
    for _, row in df.iterrows():
        name = STOCKS.get(row['symbol'], row['symbol'])
        pred_change = ((row['predicted_close'] - row['close']) / row['close'] * 100) if pd.notna(row['predicted_close']) else 0
        stocks_desc.append(f"- {name}({row['symbol']}): 当前{row['close']:.2f}, 预测{pred_change:+.1f}%, RSI{row['rsi6']:.0f}")
    
    prompt = f"""请分析以下股票组合：

{chr(10).join(stocks_desc)}

请给出：
1. 组合整体风险评估
2. 短期（1-3天）配置建议
3. 哪只最值得买入，哪只需要减仓
4. 需要关注的风险点

控制在250字以内。"""
    
    return call_llm(prompt)

def save_analysis(symbol, analysis_type, content):
    """保存分析结果"""
    # 解析情绪和推荐
    sentiment = "中性"
    if "上涨" in content or "买入" in content or "看好" in content:
        sentiment = "乐观"
    elif "下跌" in content or "卖出" in content or "看空" in content:
        sentiment = "悲观"
    
    recommendation = "持有"
    if "买入" in content:
        recommendation = "买入"
    elif "卖出" in content:
        recommendation = "卖出"
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO llm_analysis (symbol, date, analysis_type, content, sentiment, recommendation, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, datetime.now().strftime('%Y-%m-%d'), analysis_type, content, sentiment, recommendation, 0.8))
    conn.commit()
    conn.close()

def run_all_analysis():
    """运行所有分析"""
    print("开始大模型分析...\n")
    
    for symbol in STOCKS.keys():
        name = STOCKS[symbol]
        print(f"分析 {name}({symbol})...")
        
        # 技术分析
        print("  技术分析...")
        tech_analysis = analyze_technical(symbol)
        if tech_analysis:
            save_analysis(symbol, "technical", tech_analysis)
            print(f"  ✓ 完成")
        
        # 预测分析
        print("  预测分析...")
        pred_analysis = analyze_prediction(symbol)
        if pred_analysis:
            save_analysis(symbol, "prediction", pred_analysis)
            print(f"  ✓ 完成")
    
    # 组合分析
    print("\n组合分析...")
    portfolio_analysis = analyze_portfolio()
    if portfolio_analysis:
        save_analysis("PORTFOLIO", "portfolio", portfolio_analysis)
        print("  ✓ 完成")
    
    print("\n大模型分析完成！")

def show_latest_analysis():
    """显示最新分析"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT symbol, analysis_type, content, sentiment, recommendation
        FROM llm_analysis
        WHERE date = (SELECT MAX(date) FROM llm_analysis)
        ORDER BY symbol, analysis_type
    ''', conn)
    conn.close()
    
    if df.empty:
        print("暂无分析结果")
    else:
        for _, row in df.iterrows():
            print(f"\n{'='*50}")
            print(f"{row['symbol']} | {row['analysis_type']} | {row['sentiment']}")
            print(f"推荐: {row['recommendation']}")
            print(f"{'='*50}")
            print(row['content'])

if __name__ == "__main__":
    import sys
    
    init_llm_tables()
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run_all_analysis()
    elif len(sys.argv) > 1 and sys.argv[1] == "show":
        show_latest_analysis()
    else:
        print("用法: python3 stock_llm_analysis.py [run|show]")
