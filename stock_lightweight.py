#!/usr/bin/env python3
"""
轻量级股票分析系统
针对低内存/小硬盘环境优化
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

# 内存优化配置
MAX_HISTORY_DAYS = 30  # 只保留30天数据
MAX_STOCKS = 10        # 最多10只股票
CACHE_SIZE = 100       # SQLite缓存页数

class LightweightStockAnalyzer:
    """轻量级股票分析器"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.optimize_db()
    
    def optimize_db(self):
        """数据库优化"""
        conn = sqlite3.connect(self.db_path)
        
        # 设置缓存大小
        conn.execute(f'PRAGMA cache_size = {CACHE_SIZE}')
        
        # 清理旧数据
        self.cleanup_old_data(conn)
        
        # 压缩数据库
        conn.execute('VACUUM')
        
        conn.commit()
        conn.close()
    
    def cleanup_old_data(self, conn):
        """清理过期数据"""
        cutoff_date = (datetime.now() - timedelta(days=MAX_HISTORY_DAYS)).strftime('%Y-%m-%d')
        
        tables = ['stock_prices', 'stock_minutes', 'stock_indicators', 
                  'trading_signals', 'price_predictions', 'monitor_alerts']
        
        for table in tables:
            try:
                conn.execute(f'''
                    DELETE FROM {table} 
                    WHERE date < ? OR created_at < ?
                ''', (cutoff_date, cutoff_date))
            except:
                pass  # 表可能不存在
        
        print(f"已清理 {cutoff_date} 之前的数据")
    
    def get_db_size(self):
        """获取数据库大小"""
        size = os.path.getsize(self.db_path)
        return f"{size / 1024 / 1024:.1f} MB"
    
    def memory_efficient_analysis(self, symbol):
        """内存高效分析"""
        conn = sqlite3.connect(self.db_path)
        
        # 只读取必要数据（最近30天）
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        df = pd.read_sql_query('''
            SELECT * FROM stock_prices 
            WHERE symbol = ? AND date >= ?
            ORDER BY date
        ''', conn, params=(symbol, cutoff))
        
        conn.close()
        
        if len(df) < 10:
            return None
        
        # 只计算核心指标
        close = df['close']
        
        # 简化指标计算
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).min_periods(5).mean().iloc[-1]
        
        # RSI简化版
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(6).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(6).mean().iloc[-1]
        rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 50
        
        # 简单评分
        score = 50
        if close.iloc[-1] > ma5: score += 20
        if close.iloc[-1] > ma20: score += 20
        if rsi < 30: score += 10  # 超卖反弹
        if rsi > 70: score -= 10  # 超买回调
        
        return {
            'symbol': symbol,
            'price': close.iloc[-1],
            'ma5': ma5,
            'ma20': ma20,
            'rsi': rsi,
            'score': score,
            'recommendation': '买入' if score > 70 else '卖出' if score < 30 else '持有'
        }
    
    def run_lightweight_monitor(self):
        """轻量级监控"""
        print(f"\n{'='*50}")
        print("🎯 轻量级股票监控")
        print(f"数据库大小: {self.get_db_size()}")
        print(f"{'='*50}\n")
        
        stocks = ['600104', '600150', '600326', '600581', '603577', '600410']
        
        for symbol in stocks:
            result = self.memory_efficient_analysis(symbol)
            if result:
                print(f"{symbol}: ¥{result['price']:.2f} | "
                      f"评分:{result['score']:.0f} | "
                      f"{result['recommendation']}")

if __name__ == "__main__":
    analyzer = LightweightStockAnalyzer()
    analyzer.run_lightweight_monitor()
    
    print(f"\n💾 数据库大小: {analyzer.get_db_size()}")
    print("✅ 轻量级分析完成")
