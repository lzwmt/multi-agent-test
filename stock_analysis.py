#!/usr/bin/env python3
"""
股票技术分析指标计算
为 MindsDB 提供技术指标数据
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

def init_analysis_tables():
    """初始化分析表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 技术指标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            close REAL,
            volume INTEGER,
            -- 移动平均线
            ma5 REAL,
            ma10 REAL,
            ma20 REAL,
            -- RSI
            rsi6 REAL,
            rsi12 REAL,
            rsi24 REAL,
            -- MACD
            macd_dif REAL,
            macd_dea REAL,
            macd_bar REAL,
            -- 布林带
            boll_upper REAL,
            boll_mid REAL,
            boll_lower REAL,
            -- 其他指标
            volatility REAL,
            price_change_pct REAL,
            volume_ma5 REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    # 交易信号表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            signal_type TEXT,
            signal_desc TEXT,
            confidence REAL,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("分析表初始化完成")

def calculate_ma(series, window):
    """计算移动平均线"""
    return series.rolling(window=window).mean()

def calculate_rsi(series, window=14):
    """计算 RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    """计算 MACD"""
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    bar = (dif - dea) * 2
    return dif, dea, bar

def calculate_bollinger(series, window=20, num_std=2):
    """计算布林带"""
    mid = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = mid + (std * num_std)
    lower = mid - (std * num_std)
    return upper, mid, lower

def analyze_stock(symbol):
    """分析单只股票"""
    conn = sqlite3.connect(DB_PATH)
    
    # 获取历史数据
    df = pd.read_sql_query(
        "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
        conn, params=(symbol,)
    )
    
    if len(df) < 30:
        print(f"{symbol}: 数据不足")
        conn.close()
        return
    
    print(f"分析 {symbol}: {len(df)} 条数据")
    
    # 计算指标
    df['ma5'] = calculate_ma(df['close'], 5)
    df['ma10'] = calculate_ma(df['close'], 10)
    df['ma20'] = calculate_ma(df['close'], 20)
    
    df['rsi6'] = calculate_rsi(df['close'], 6)
    df['rsi12'] = calculate_rsi(df['close'], 12)
    df['rsi24'] = calculate_rsi(df['close'], 24)
    
    df['macd_dif'], df['macd_dea'], df['macd_bar'] = calculate_macd(df['close'])
    
    df['boll_upper'], df['boll_mid'], df['boll_lower'] = calculate_bollinger(df['close'])
    
    # 波动率（20日）
    df['volatility'] = df['close'].pct_change().rolling(window=20).std() * 100
    
    # 价格变化率
    df['price_change_pct'] = df['close'].pct_change() * 100
    
    # 成交量MA5
    df['volume_ma5'] = calculate_ma(df['volume'], 5)
    
    # 存储指标
    indicator_cols = ['symbol', 'date', 'close', 'volume', 'ma5', 'ma10', 'ma20',
                      'rsi6', 'rsi12', 'rsi24', 'macd_dif', 'macd_dea', 'macd_bar',
                      'boll_upper', 'boll_mid', 'boll_lower', 'volatility',
                      'price_change_pct', 'volume_ma5']
    
    indicators_df = df[indicator_cols].dropna()
    
    for _, row in indicators_df.iterrows():
        conn.execute('''
            INSERT OR REPLACE INTO stock_indicators
            (symbol, date, close, volume, ma5, ma10, ma20, rsi6, rsi12, rsi24,
             macd_dif, macd_dea, macd_bar, boll_upper, boll_mid, boll_lower,
             volatility, price_change_pct, volume_ma5)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(row))
    
    # 生成交易信号
    signals = generate_signals(df)
    for signal in signals:
        conn.execute('''
            INSERT INTO trading_signals
            (symbol, date, signal_type, signal_desc, confidence, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', signal)
    
    conn.commit()
    conn.close()
    
    print(f"  存储 {len(indicators_df)} 条指标数据")
    print(f"  生成 {len(signals)} 个交易信号")

def generate_signals(df):
    """生成交易信号"""
    signals = []
    
    if len(df) < 2:
        return signals
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # MACD 金叉/死叉
    if prev['macd_dif'] < prev['macd_dea'] and latest['macd_dif'] > latest['macd_dea']:
        signals.append((
            latest['symbol'], latest['date'], 'MACD_GOLDEN_CROSS',
            'MACD金叉，买入信号', 0.7, latest['close']
        ))
    elif prev['macd_dif'] > prev['macd_dea'] and latest['macd_dif'] < latest['macd_dea']:
        signals.append((
            latest['symbol'], latest['date'], 'MACD_DEATH_CROSS',
            'MACD死叉，卖出信号', 0.7, latest['close']
        ))
    
    # RSI 超买/超卖
    if latest['rsi6'] < 30:
        signals.append((
            latest['symbol'], latest['date'], 'RSI_OVERSOLD',
            f'RSI超卖({latest["rsi6"]:.1f})，可能反弹', 0.6, latest['close']
        ))
    elif latest['rsi6'] > 70:
        signals.append((
            latest['symbol'], latest['date'], 'RSI_OVERBOUGHT',
            f'RSI超买({latest["rsi6"]:.1f})，可能回调', 0.6, latest['close']
        ))
    
    # 均线多头排列/空头排列
    if latest['ma5'] > latest['ma10'] > latest['ma20']:
        if prev['ma5'] <= prev['ma10']:
            signals.append((
                latest['symbol'], latest['date'], 'MA_BULLISH',
                '均线多头排列形成，趋势向上', 0.75, latest['close']
            ))
    elif latest['ma5'] < latest['ma10'] < latest['ma20']:
        if prev['ma5'] >= prev['ma10']:
            signals.append((
                latest['symbol'], latest['date'], 'MA_BEARISH',
                '均线空头排列形成，趋势向下', 0.75, latest['close']
            ))
    
    # 布林带突破
    if latest['close'] > latest['boll_upper']:
        signals.append((
            latest['symbol'], latest['date'], 'BOLL_UPPER_BREAK',
            '突破布林带上轨，强势', 0.65, latest['close']
        ))
    elif latest['close'] < latest['boll_lower']:
        signals.append((
            latest['symbol'], latest['date'], 'BOLL_LOWER_BREAK',
            '跌破布林带下轨，弱势', 0.65, latest['close']
        ))
    
    return signals

def analyze_all():
    """分析所有股票"""
    conn = sqlite3.connect(DB_PATH)
    symbols = pd.read_sql_query(
        "SELECT DISTINCT symbol FROM stock_prices", conn
    )['symbol'].tolist()
    conn.close()
    
    print(f"开始分析 {len(symbols)} 只股票...\n")
    for symbol in symbols:
        try:
            analyze_stock(symbol)
        except Exception as e:
            print(f"分析 {symbol} 失败: {e}")
    
    print("\n分析完成！")

def show_latest_signals():
    """显示最新信号"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT symbol, date, signal_type, signal_desc, confidence, price
        FROM trading_signals
        WHERE date = (SELECT MAX(date) FROM trading_signals)
        ORDER BY confidence DESC
    ''', conn)
    conn.close()
    
    if df.empty:
        print("暂无交易信号")
    else:
        print("\n最新交易信号:")
        print(df.to_string(index=False))

def show_indicators(symbol):
    """显示最新指标"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT symbol, date, close, ma5, ma10, ma20, rsi6, macd_bar, boll_upper, boll_lower
        FROM stock_indicators
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 5
    ''', conn, params=(symbol,))
    conn.close()
    
    print(f"\n{symbol} 最新指标:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    import sys
    
    init_analysis_tables()
    
    if len(sys.argv) > 1 and sys.argv[1] == "signals":
        show_latest_signals()
    elif len(sys.argv) > 1 and sys.argv[1] == "indicators":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "600104"
        show_indicators(symbol)
    else:
        analyze_all()
