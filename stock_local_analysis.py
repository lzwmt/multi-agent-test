#!/usr/bin/env python3
"""
本地规则-based 股票分析
无需API调用，基于技术指标生成分析报告
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

STOCKS = {
    '600104': '上汽集团',
    '600150': '中国船舶',
    '600326': '西藏天路',
    '600581': '八一钢铁',
    '603577': '汇金通',
}

def init_analysis_tables():
    """初始化分析表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comprehensive_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            technical_summary TEXT,
            prediction_summary TEXT,
            signal_summary TEXT,
            recommendation TEXT,
            risk_level TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def analyze_stock(symbol):
    """综合分析单只股票"""
    conn = sqlite3.connect(DB_PATH)
    name = STOCKS.get(symbol, symbol)
    
    # 获取最新指标
    indicators = pd.read_sql_query('''
        SELECT * FROM stock_indicators 
        WHERE symbol = ? ORDER BY date DESC LIMIT 1
    ''', conn, params=(symbol,))
    
    # 获取预测
    prediction = pd.read_sql_query('''
        SELECT * FROM price_predictions 
        WHERE symbol = ? ORDER BY created_at DESC LIMIT 1
    ''', conn, params=(symbol,))
    
    # 获取信号
    signals = pd.read_sql_query('''
        SELECT * FROM trading_signals 
        WHERE symbol = ? ORDER BY date DESC LIMIT 3
    ''', conn, params=(symbol,))
    
    conn.close()
    
    if indicators.empty:
        return None
    
    ind = indicators.iloc[0]
    
    # 技术分析
    tech_analysis = []
    
    # 趋势判断
    if ind['ma5'] > ind['ma10'] > ind['ma20']:
        trend = "多头排列，趋势向上"
    elif ind['ma5'] < ind['ma10'] < ind['ma20']:
        trend = "空头排列，趋势向下"
    else:
        trend = "均线纠缠，趋势不明"
    tech_analysis.append(f"趋势：{trend}")
    
    # RSI
    if ind['rsi6'] > 70:
        rsi_status = f"RSI超买({ind['rsi6']:.0f})，注意回调风险"
    elif ind['rsi6'] < 30:
        rsi_status = f"RSI超卖({ind['rsi6']:.0f})，可能反弹"
    else:
        rsi_status = f"RSI正常({ind['rsi6']:.0f})"
    tech_analysis.append(rsi_status)
    
    # MACD
    macd_status = "MACD金叉" if ind['macd_bar'] > 0 else "MACD死叉"
    tech_analysis.append(macd_status)
    
    # 预测分析
    pred_analysis = ""
    if not prediction.empty:
        pred = prediction.iloc[0]
        change = ((pred['predicted_close'] - ind['close']) / ind['close'] * 100)
        direction = "上涨" if change > 0 else "下跌"
        pred_analysis = f"AI预测明日{direction}{abs(change):.1f}% (置信度{pred['confidence']*100:.0f}%)"
    
    # 信号汇总
    signal_text = []
    if not signals.empty:
        for _, sig in signals.iterrows():
            signal_text.append(f"{sig['signal_type']}: {sig['signal_desc']}")
    
    # 综合推荐
    buy_score = 0
    if ind['ma5'] > ind['ma10']: buy_score += 1
    if ind['macd_bar'] > 0: buy_score += 1
    if ind['rsi6'] < 50: buy_score += 1
    if not prediction.empty and change > 0: buy_score += 1
    
    if buy_score >= 3:
        recommendation = "买入"
    elif buy_score <= 1:
        recommendation = "卖出"
    else:
        recommendation = "持有"
    
    # 风险等级
    volatility = ind.get('volatility', 0) or 0
    if volatility > 5:
        risk = "高"
    elif volatility > 3:
        risk = "中"
    else:
        risk = "低"
    
    return {
        'symbol': symbol,
        'name': name,
        'date': ind['date'],
        'close': ind['close'],
        'technical': " | ".join(tech_analysis),
        'prediction': pred_analysis,
        'signals': "; ".join(signal_text) if signal_text else "无",
        'recommendation': recommendation,
        'risk': risk,
        'confidence': buy_score / 4
    }

def generate_report():
    """生成分析报告"""
    init_analysis_tables()
    
    print("=" * 60)
    print("股票综合分析报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    for symbol in STOCKS.keys():
        result = analyze_stock(symbol)
        if not result:
            continue
        
        print(f"\n【{result['name']} ({symbol})】")
        print(f"当前价: ¥{result['close']:.2f}")
        print(f"技术面: {result['technical']}")
        print(f"AI预测: {result['prediction']}")
        print(f"交易信号: {result['signals']}")
        print(f"建议操作: 【{result['recommendation']}】")
        print(f"风险等级: {result['risk']}")
        
        # 存入数据库
        conn.execute('''
            INSERT INTO comprehensive_analysis 
            (symbol, date, technical_summary, prediction_summary, signal_summary, 
             recommendation, risk_level, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, result['date'], result['technical'], result['prediction'], 
              result['signals'], result['recommendation'], result['risk'], result['confidence']))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("报告已保存到 comprehensive_analysis 表")
    print("=" * 60)

def show_mindsdb_report():
    """显示MindsDB可查询的报告"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT symbol, date, recommendation, risk_level, confidence
        FROM comprehensive_analysis
        WHERE date = (SELECT MAX(date) FROM comprehensive_analysis)
        ORDER BY confidence DESC
    ''', conn)
    conn.close()
    
    print("\nMindsDB 查询结果:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "mindsdb":
        show_mindsdb_report()
    else:
        generate_report()
