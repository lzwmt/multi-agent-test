#!/usr/bin/env python3
"""
MindsDB + AKShare 实时数据桥接
支持分钟级数据更新
"""

import akshare as ak
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

STOCKS = [
    ('600104', '上汽集团'),
    ('600150', '中国船舶'),
    ('600326', '西藏天路'),
    ('600581', '八一钢铁'),
    ('603577', '汇金通'),
    ('600410', '华胜天成'),
]

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 日线数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume INTEGER,
            amount REAL,
            amplitude REAL,
            change_pct REAL,
            change_amount REAL,
            turnover REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分钟数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_minutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            datetime TEXT,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume INTEGER,
            amount REAL,
            change_pct REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, datetime)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON stock_prices(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON stock_prices(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_prices(symbol, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_min_symbol ON stock_minutes(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_min_datetime ON stock_minutes(datetime)')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

def fetch_minute_data(symbol, period="1", days=1):
    """获取分钟级数据"""
    try:
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust="qfq")
        if df.empty:
            return pd.DataFrame()
        
        # 只保留最近 N 天
        df['日期时间'] = pd.to_datetime(df['日期时间'])
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['日期时间'] >= cutoff]
        
        return df
    except Exception as e:
        print(f"获取 {symbol} 分钟数据失败: {e}")
        return pd.DataFrame()

def update_minute_data(symbol, name, days=1):
    """更新分钟数据"""
    print(f"更新 {symbol} ({name}) 分钟数据...")
    
    df = fetch_minute_data(symbol, period="1", days=days)
    if df.empty:
        print(f"  无新数据")
        return 0
    
    # 处理数据
    df = df.rename(columns={
        '时间': 'datetime',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount',
    })
    
    df['symbol'] = symbol
    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M')
    
    columns = ['symbol', 'datetime', 'open', 'close', 'high', 'low', 'volume', 'amount']
    df = df[columns]
    
    # 存入数据库（UPSERT）
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO stock_minutes 
                (symbol, datetime, open, close, high, low, volume, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(row))
            count += 1
        except Exception as e:
            print(f"  插入失败: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"  更新 {count} 条分钟数据")
    return count

def update_all_minutes(days=1):
    """更新所有股票的分钟数据"""
    total = 0
    for symbol, name in STOCKS:
        try:
            count = update_minute_data(symbol, name, days)
            total += count
        except Exception as e:
            print(f"更新 {symbol} 失败: {e}")
    
    print(f"\n总计更新 {total} 条分钟数据")
    return total

def get_last_date(symbol):
    """获取某股票最新数据日期"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(date) FROM stock_prices WHERE symbol = ?', (symbol,))
    result = cursor.fetchone()[0]
    conn.close()
    return result

def fetch_daily_data(symbol, start_date, end_date):
    """从 AKShare 获取日线数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily",
            start_date=start_date,
            end_date=end_date
        )
        return df
    except Exception as e:
        print(f"获取 {symbol} 数据失败: {e}")
        return pd.DataFrame()

def process_and_store_daily(df, symbol):
    """处理并存储日线数据"""
    if df.empty:
        return 0
    
    df = df.rename(columns={
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount',
        '振幅': 'amplitude',
        '涨跌幅': 'change_pct',
        '涨跌额': 'change_amount',
        '换手率': 'turnover'
    })
    
    df['symbol'] = symbol
    
    columns = ['symbol', 'date', 'open', 'close', 'high', 'low',
               'volume', 'amount', 'amplitude', 'change_pct', 'change_amount', 'turnover']
    df = df[columns]
    
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('stock_prices', conn, if_exists='append', index=False)
    conn.close()
    
    return len(df)

def incremental_update_daily(symbol, name):
    """增量更新日线数据"""
    last_date = get_last_date(symbol)
    
    if last_date:
        start = datetime.strptime(last_date, '%Y-%m-%d')
        start_date = (start + timedelta(days=1)).strftime('%Y%m%d')
    else:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    
    end_date = datetime.now().strftime('%Y%m%d')
    
    if start_date > end_date:
        return 0
    
    df = fetch_daily_data(symbol, start_date, end_date)
    count = process_and_store_daily(df, symbol)
    return count

def update_all_daily():
    """更新所有日线数据"""
    total = 0
    for symbol, name in STOCKS:
        try:
            count = incremental_update_daily(symbol, name)
            total += count
        except Exception as e:
            print(f"更新 {symbol} 失败: {e}")
    return total

def get_realtime_spot():
    """获取实时行情快照"""
    print("获取实时行情...")
    df = ak.stock_zh_a_spot()
    symbols = [s[0] for s in STOCKS]
    df_filtered = df[df['代码'].isin(symbols)]
    return df_filtered[['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额']]

def show_stats():
    """显示数据统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM stock_prices')
    daily_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stock_minutes')
    minute_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_prices')
    daily_symbols = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_minutes')
    minute_symbols = cursor.fetchone()[0]
    
    cursor.execute('SELECT MAX(date) FROM stock_prices')
    latest_daily = cursor.fetchone()[0]
    
    cursor.execute('SELECT MAX(datetime) FROM stock_minutes')
    latest_minute = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n数据统计:")
    print(f"  日线数据: {daily_symbols} 只股票, {daily_total} 条记录, 最新: {latest_daily}")
    print(f"  分钟数据: {minute_symbols} 只股票, {minute_total} 条记录, 最新: {latest_minute}")

if __name__ == "__main__":
    init_database()
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    
    if mode == "minute":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        print(f"执行分钟级更新（最近{days}天）...")
        update_all_minutes(days=days)
    elif mode == "daily":
        print("执行日线增量更新...")
        update_all_daily()
    elif mode == "full":
        print("执行日线全量更新...")
        for symbol, name in STOCKS:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stock_prices WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()
            fetch_daily_data(symbol, 
                           (datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                           datetime.now().strftime('%Y%m%d'))
    elif mode == "realtime":
        df = get_realtime_spot()
        print(df.to_string(index=False))
    elif mode == "stats":
        show_stats()
    else:
        print("用法: python3 mindsdb_akshare_bridge.py [daily|minute|full|realtime|stats]")
        print("  daily    - 日线增量更新")
        print("  minute   - 分钟级更新")
        print("  full     - 日线全量更新")
        print("  realtime - 实时行情快照")
        print("  stats    - 查看统计")
