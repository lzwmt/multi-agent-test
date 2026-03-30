#!/usr/bin/env python3
"""
实时股票盯盘系统
支持价格监控、异动检测、自动告警
"""

import akshare as ak
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import sys
import os

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

# 监控配置
WATCH_LIST = [
    {'symbol': '600104', 'name': '上汽集团', 'alert_high': 15.0, 'alert_low': 12.0},
    {'symbol': '600150', 'name': '中国船舶', 'alert_high': 40.0, 'alert_low': 35.0},
    {'symbol': '600326', 'name': '西藏天路', 'alert_high': 12.0, 'alert_low': 9.0},
    {'symbol': '600581', 'name': '八一钢铁', 'alert_high': 3.2, 'alert_low': 2.5},
    {'symbol': '603577', 'name': '汇金通', 'alert_high': 13.0, 'alert_low': 11.0},
]

class StockMonitor:
    """股票实时监控系统"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_tables()
        self.last_alert = {}  # 防止重复告警
    
    def init_tables(self):
        """初始化监控表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 实时行情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                name TEXT,
                price REAL,
                change_pct REAL,
                volume INTEGER,
                amount REAL,
                high REAL,
                low REAL,
                open REAL,
                pre_close REAL,
                quote_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 告警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                alert_type TEXT,
                alert_msg TEXT,
                price REAL,
                threshold REAL,
                is_triggered BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 异动记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abnormal_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                move_type TEXT,
                change_pct REAL,
                volume_ratio REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_realtime_spot(self):
        """获取实时行情快照"""
        try:
            df = ak.stock_zh_a_spot()
            return df
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def filter_watchlist(self, df):
        """筛选自选股"""
        symbols = [s['symbol'] for s in WATCH_LIST]
        return df[df['代码'].isin(symbols)].copy()
    
    def store_quotes(self, df):
        """存储实时行情"""
        if df is None or df.empty:
            return
        
        conn = sqlite3.connect(self.db_path)
        
        for _, row in df.iterrows():
            conn.execute('''
                INSERT INTO realtime_quotes 
                (symbol, name, price, change_pct, volume, amount, high, low, open, pre_close, quote_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['代码'],
                row['名称'],
                row['最新价'],
                row['涨跌幅'],
                row['成交量'],
                row['成交额'],
                row['最高'],
                row['最低'],
                row['今开'],
                row['昨收'],
                datetime.now().strftime('%H:%M:%S')
            ))
        
        conn.commit()
        conn.close()
    
    def check_price_alerts(self, df):
        """检查价格告警"""
        if df is None or df.empty:
            return []
        
        alerts = []
        now = datetime.now()
        
        for watch in WATCH_LIST:
            symbol = watch['symbol']
            row = df[df['代码'] == symbol]
            
            if row.empty:
                continue
            
            price = row.iloc[0]['最新价']
            change_pct = row.iloc[0]['涨跌幅']
            name = watch['name']
            
            # 检查高价告警
            if price >= watch['alert_high']:
                alert_key = f"{symbol}_high"
                if alert_key not in self.last_alert or (now - self.last_alert.get(alert_key, datetime.min)).seconds > 300:
                    alerts.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'PRICE_HIGH',
                        'msg': f'🔴 {name}({symbol}) 突破高价预警线 ¥{watch["alert_high"]}，当前 ¥{price:.2f}',
                        'price': price,
                        'threshold': watch['alert_high']
                    })
                    self.last_alert[alert_key] = now
            
            # 检查低价告警
            if price <= watch['alert_low']:
                alert_key = f"{symbol}_low"
                if alert_key not in self.last_alert or (now - self.last_alert.get(alert_key, datetime.min)).seconds > 300:
                    alerts.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'PRICE_LOW',
                        'msg': f'🟢 {name}({symbol}) 跌破低价预警线 ¥{watch["alert_low"]}，当前 ¥{price:.2f}',
                        'price': price,
                        'threshold': watch['alert_low']
                    })
                    self.last_alert[alert_key] = now
            
            # 检查涨跌停
            if change_pct >= 9.5:
                alert_key = f"{symbol}_limit_up"
                if alert_key not in self.last_alert or (now - self.last_alert.get(alert_key, datetime.min)).seconds > 600:
                    alerts.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'LIMIT_UP',
                        'msg': f'🚀 {name}({symbol}) 触及涨停！+{change_pct:.2f}%',
                        'price': price,
                        'threshold': change_pct
                    })
                    self.last_alert[alert_key] = now
            
            if change_pct <= -9.5:
                alert_key = f"{symbol}_limit_down"
                if alert_key not in self.last_alert or (now - self.last_alert.get(alert_key, datetime.min)).seconds > 600:
                    alerts.append({
                        'symbol': symbol,
                        'name': name,
                        'type': 'LIMIT_DOWN',
                        'msg': f'💥 {name}({symbol}) 触及跌停！{change_pct:.2f}%',
                        'price': price,
                        'threshold': change_pct
                    })
                    self.last_alert[alert_key] = now
        
        return alerts
    
    def check_abnormal_moves(self, df):
        """检查异动"""
        if df is None or df.empty:
            return []
        
        moves = []
        
        for _, row in df.iterrows():
            symbol = row['代码']
            change_pct = row['涨跌幅']
            volume_ratio = row.get('量比', 1)
            name = row['名称']
            
            # 大幅波动
            if abs(change_pct) >= 5:
                moves.append({
                    'symbol': symbol,
                    'name': name,
                    'type': 'BIG_MOVE',
                    'change_pct': change_pct,
                    'volume_ratio': volume_ratio,
                    'desc': f'{"大涨" if change_pct > 0 else "大跌"} {abs(change_pct):.2f}%'
                })
            
            # 成交量异常
            if volume_ratio >= 3:
                moves.append({
                    'symbol': symbol,
                    'name': name,
                    'type': 'VOLUME_SPIKE',
                    'change_pct': change_pct,
                    'volume_ratio': volume_ratio,
                    'desc': f'成交量放大 {volume_ratio:.1f} 倍'
                })
        
        return moves
    
    def store_alerts(self, alerts):
        """存储告警"""
        if not alerts:
            return
        
        conn = sqlite3.connect(self.db_path)
        
        for alert in alerts:
            conn.execute('''
                INSERT INTO price_alerts (symbol, alert_type, alert_msg, price, threshold, is_triggered)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (alert['symbol'], alert['type'], alert['msg'], alert['price'], alert['threshold']))
        
        conn.commit()
        conn.close()
    
    def store_moves(self, moves):
        """存储异动"""
        if not moves:
            return
        
        conn = sqlite3.connect(self.db_path)
        
        for move in moves:
            conn.execute('''
                INSERT INTO abnormal_moves (symbol, move_type, change_pct, volume_ratio, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (move['symbol'], move['type'], move['change_pct'], move['volume_ratio'], move['desc']))
        
        conn.commit()
        conn.close()
    
    def display_realtime(self, df):
        """显示实时行情"""
        if df is None or df.empty:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 实时行情")
        print("-" * 70)
        print(f"{'股票':<12} {'价格':>8} {'涨跌%':>8} {'成交量':>12} {'状态':<10}")
        print("-" * 70)
        
        for _, row in df.iterrows():
            symbol = row['代码']
            name = row['名称'][:6]
            price = row['最新价']
            change = row['涨跌幅']
            volume = row['成交量'] / 10000  # 万手
            
            # 状态标识
            if change >= 9.5:
                status = "🔥涨停"
            elif change <= -9.5:
                status = "💥跌停"
            elif change >= 5:
                status = "🚀大涨"
            elif change <= -5:
                status = "📉大跌"
            elif change > 0:
                status = "📈上涨"
            else:
                status = "📉下跌"
            
            change_str = f"{change:+.2f}%"
            
            print(f"{name}({symbol})", end=' ')
            print(f"{price:>8.2f} {change_str:>8} {volume:>10.0f}万 {status:<10}")
        
        print("-" * 70)
    
    def run_monitor_cycle(self):
        """运行一次监控周期"""
        # 获取实时行情
        df = self.get_realtime_spot()
        
        if df is None:
            print("获取行情失败，跳过本次监控")
            return
        
        # 筛选自选股
        watch_df = self.filter_watchlist(df)
        
        # 存储行情
        self.store_quotes(watch_df)
        
        # 显示行情
        self.display_realtime(watch_df)
        
        # 检查告警
        alerts = self.check_price_alerts(watch_df)
        if alerts:
            print("\n⚠️  价格告警:")
            for alert in alerts:
                print(f"   {alert['msg']}")
            self.store_alerts(alerts)
        
        # 检查异动
        moves = self.check_abnormal_moves(watch_df)
        if moves:
            print("\n📊 异动检测:")
            for move in moves:
                print(f"   {move['name']}({move['symbol']}): {move['desc']}")
            self.store_moves(moves)
    
    def continuous_monitor(self, interval=60):
        """持续监控"""
        print(f"\n{'='*70}")
        print("🎯 实时股票盯盘系统启动")
        print(f"监控股票: {len(WATCH_LIST)} 只")
        print(f"刷新间隔: {interval} 秒")
        print(f"{'='*70}\n")
        
        try:
            while True:
                self.run_monitor_cycle()
                print(f"\n⏱️  {interval}秒后刷新... (Ctrl+C停止)")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n✋ 监控已停止")
    
    def show_monitor_stats(self):
        """显示监控统计"""
        conn = sqlite3.connect(self.db_path)
        
        # 最新行情
        quotes = pd.read_sql_query('''
            SELECT symbol, name, price, change_pct, quote_time
            FROM realtime_quotes
            WHERE created_at >= datetime('now', '-1 hour')
            GROUP BY symbol
            HAVING quote_time = MAX(quote_time)
            ORDER BY change_pct DESC
        ''', conn)
        
        # 今日告警
        alerts = pd.read_sql_query('''
            SELECT symbol, alert_type, alert_msg, created_at
            FROM price_alerts
            WHERE date(created_at) = date('now')
            ORDER BY created_at DESC
            LIMIT 10
        ''', conn)
        
        # 今日异动
        moves = pd.read_sql_query('''
            SELECT symbol, move_type, change_pct, description, created_at
            FROM abnormal_moves
            WHERE date(created_at) = date('now')
            ORDER BY created_at DESC
            LIMIT 10
        ''', conn)
        
        conn.close()
        
        print("\n" + "="*70)
        print("📈 监控统计")
        print("="*70)
        
        if not quotes.empty:
            print("\n最新行情:")
            print(quotes.to_string(index=False))
        
        if not alerts.empty:
            print("\n今日告警:")
            print(alerts.to_string(index=False))
        
        if not moves.empty:
            print("\n今日异动:")
            print(moves.to_string(index=False))

if __name__ == "__main__":
    monitor = StockMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            monitor.continuous_monitor(interval)
        elif sys.argv[1] == "once":
            monitor.run_monitor_cycle()
        elif sys.argv[1] == "stats":
            monitor.show_monitor_stats()
        else:
            print("用法: python3 stock_monitor.py [start [间隔秒数]|once|stats]")
    else:
        # 默认运行一次
        monitor.run_monitor_cycle()
