#!/usr/bin/env python3
"""
实时股票盯盘系统 (本地数据版)
基于已有数据模拟实时监控
支持 Discord 通知和定时刷新
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import json
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realtime_data import RealtimeDataSource

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

# Discord Webhook 配置（从环境变量读取）
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK_URL', None)

WATCH_LIST = [
    {'symbol': '600104', 'name': '上汽集团'},
    {'symbol': '600150', 'name': '中国船舶'},
    {'symbol': '600326', 'name': '西藏天路'},
    {'symbol': '600581', 'name': '八一钢铁'},
    {'symbol': '603577', 'name': '汇金通'},
    {'symbol': '600410', 'name': '华胜天成'},
]

class LocalStockMonitor:
    """基于本地数据的盯盘系统"""
    
    def __init__(self, discord_webhook=None):
        self.db_path = DB_PATH
        self.discord_webhook = discord_webhook or DISCORD_WEBHOOK
        self.init_tables()
    
    def init_tables(self):
        """初始化监控表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                alert_type TEXT,
                price REAL,
                threshold REAL,
                message TEXT,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def send_discord_notification(self, message, alert_type="info"):
        """发送 Discord 通知"""
        if not self.discord_webhook:
            print("  [通知] Discord Webhook 未配置，跳过通知")
            return False
        
        # 根据类型设置颜色和 emoji
        colors = {
            "PRICE_HIGH": 16776960,    # 黄色 - 高价预警
            "PRICE_LOW": 3447003,      # 蓝色 - 低价预警
            "LIMIT_UP": 3066993,       # 绿色 - 涨停
            "LIMIT_DOWN": 15158332,    # 红色 - 跌停
            "BIG_MOVE": 16711680,      # 橙色 - 大幅波动
            "info": 3447003            # 蓝色 - 普通信息
        }
        
        emoji = "📊"
        color = colors.get(alert_type, colors["info"])
        
        if "涨停" in message:
            emoji = "🚀"
            color = colors["LIMIT_UP"]
        elif "跌停" in message:
            emoji = "💥"
            color = colors["LIMIT_DOWN"]
        elif "突破" in message or "跌破" in message:
            emoji = "⚠️"
            color = colors["PRICE_HIGH"] if "突破" in message else colors["PRICE_LOW"]
        elif "大涨" in message:
            emoji = "📈"
            color = colors["BIG_MOVE"]
        elif "大跌" in message:
            emoji = "📉"
            color = colors["BIG_MOVE"]
        
        payload = {
            "embeds": [{
                "title": f"{emoji} 股票盯盘告警",
                "description": message,
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "股票盯盘系统 · " + datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            }]
        }
        
        try:
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            if response.status_code == 204:
                print(f"  [通知] Discord 通知已发送 ✓")
                return True
            else:
                print(f"  [通知] Discord 发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"  [通知] 发送异常：{e}")
            return False
    
    def calculate_alert_levels(self, symbol):
        """自动计算预警线（基于 ATR）"""
        conn = sqlite3.connect(self.db_path)
        
        # 获取最近 20 日数据
        df = pd.read_sql_query('''
            SELECT close, high, low
            FROM stock_prices
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 20
        ''', conn, params=(symbol,))
        
        conn.close()
        
        if len(df) < 10:
            return None, None
        
        # 计算 ATR (平均真实波幅)
        df = df.sort_index()
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        atr = df['tr'].mean()
        
        # 当前价格
        current_price = df.iloc[-1]['close']
        
        # 计算预警线 (基于 ATR 倍数)
        alert_high = current_price + atr * 2  # 上轨：+2 倍 ATR
        alert_low = current_price - atr * 2   # 下轨：-2 倍 ATR
        
        # 基于近期高低点的支撑压力位
        recent_high = df['high'].max()
        recent_low = df['low'].min()
        
        # 综合计算
        alert_high = max(alert_high, recent_high * 0.95)
        alert_low = min(alert_low, recent_low * 1.05)
        
        return round(alert_high, 2), round(alert_low, 2)
    
    def get_latest_prices(self, use_realtime=True):
        """获取最新价格（优先级：腾讯API → AKShare → 本地数据库）"""
        prices = {}
        
        for watch in WATCH_LIST:
            symbol = watch['symbol']
            data_found = False
            
            if use_realtime:
                # 第1优先级：腾讯API
                try:
                    result, msg = RealtimeDataSource.get_realtime(symbol, 'tencent')
                    if result:
                        alert_high, alert_low = self.calculate_alert_levels(symbol)
                        
                        prices[symbol] = {
                            'name': result['name'],
                            'price': result['price'],
                            'change_pct': result['change_pct'],
                            'date': result['timestamp'],
                            'alert_high': alert_high,
                            'alert_low': alert_low,
                            'volume': result.get('volume', 0),
                            'high': result.get('high', 0),
                            'low': result.get('low', 0),
                            'open': result.get('open', 0),
                            'source': 'tencent_api'
                        }
                        data_found = True
                        print(f"  [{symbol}] 腾讯API ✓")
                except Exception as e:
                    print(f"  [{symbol}] 腾讯API失败: {e}")
                
                # 第2优先级：AKShare（如果腾讯失败）
                if not data_found:
                    try:
                        import akshare as ak
                        df = ak.stock_zh_a_spot()
                        stock_row = df[df['代码'] == symbol]
                        
                        if not stock_row.empty:
                            alert_high, alert_low = self.calculate_alert_levels(symbol)
                            
                            prices[symbol] = {
                                'name': stock_row.iloc[0]['名称'],
                                'price': stock_row.iloc[0]['最新价'],
                                'change_pct': stock_row.iloc[0]['涨跌幅'],
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'alert_high': alert_high,
                                'alert_low': alert_low,
                                'volume': stock_row.iloc[0]['成交量'],
                                'high': stock_row.iloc[0]['最高'],
                                'low': stock_row.iloc[0]['最低'],
                                'source': 'akshare_api'
                            }
                            data_found = True
                            print(f"  [{symbol}] AKShare ✓")
                    except Exception as e:
                        print(f"  [{symbol}] AKShare失败: {e}")
            
            # 第3优先级：本地数据库（如果所有API都失败）
            if not data_found:
                try:
                    conn = sqlite3.connect(self.db_path)
                    df = pd.read_sql_query('''
                        SELECT close, change_pct, date
                        FROM stock_prices
                        WHERE symbol = ?
                        ORDER BY date DESC
                        LIMIT 1
                    ''', conn, params=(symbol,))
                    
                    if not df.empty:
                        alert_high, alert_low = self.calculate_alert_levels(symbol)
                        
                        prices[symbol] = {
                            'name': watch['name'],
                            'price': df.iloc[0]['close'],
                            'change_pct': df.iloc[0]['change_pct'],
                            'date': df.iloc[0]['date'],
                            'alert_high': alert_high,
                            'alert_low': alert_low,
                            'source': 'local_db'
                        }
                        print(f"  [{symbol}] 本地数据库 ✓")
                    
                    conn.close()
                except Exception as e:
                    print(f"  [{symbol}] 本地数据库失败: {e}")
        
        return prices
    
    def check_alerts(self, prices):
        """检查告警"""
        alerts = []
        
        for watch in WATCH_LIST:
            symbol = watch['symbol']
            if symbol not in prices:
                continue
            
            data = prices[symbol]
            price = data['price']
            change_pct = data['change_pct']
            name = data['name']
            
            alert_high = data.get('alert_high')
            alert_low = data.get('alert_low')
            
            # 高价告警
            if alert_high and price >= alert_high:
                alerts.append({
                    'symbol': symbol,
                    'type': 'PRICE_HIGH',
                    'price': price,
                    'threshold': alert_high,
                    'message': f'🔴 {name}({symbol}) 突破高价线 ¥{alert_high}，当前 ¥{price:.2f}'
                })
            
            # 低价告警
            if alert_low and price <= alert_low:
                alerts.append({
                    'symbol': symbol,
                    'type': 'PRICE_LOW',
                    'price': price,
                    'threshold': alert_low,
                    'message': f'🟢 {name}({symbol}) 跌破低价线 ¥{alert_low}，当前 ¥{price:.2f}'
                })
            
            # 涨跌停
            if change_pct >= 9.5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'LIMIT_UP',
                    'price': price,
                    'threshold': change_pct,
                    'message': f'🚀 {name}({symbol}) 触及涨停！+{change_pct:.2f}%'
                })
            
            if change_pct <= -9.5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'LIMIT_DOWN',
                    'price': price,
                    'threshold': change_pct,
                    'message': f'💥 {name}({symbol}) 触及跌停！{change_pct:.2f}%'
                })
            
            # 大幅波动
            if abs(change_pct) >= 5 and abs(change_pct) < 9.5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'BIG_MOVE',
                    'price': price,
                    'threshold': change_pct,
                    'message': f'📊 {name}({symbol}) {"大涨" if change_pct > 0 else "大跌"} {abs(change_pct):.2f}%'
                })
        
        return alerts
    
    def display_dashboard(self, prices):
        """显示盯盘面板"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📈 实时盯盘面板")
        print("=" * 70)
        print(f"{'股票':<15} {'价格':>10} {'涨跌%':>10} {'预警线':>20} {'状态':<10}")
        print("-" * 70)
        
        for watch in WATCH_LIST:
            symbol = watch['symbol']
            if symbol not in prices:
                continue
            
            data = prices[symbol]
            name = data['name']
            price = data['price']
            change = data['change_pct']
            
            # 预警线显示
            alert_high = data.get('alert_high')
            alert_low = data.get('alert_low')
            alert_range = f"¥{alert_low:.1f} - ¥{alert_high:.1f}" if alert_low and alert_high else "计算中..."
            
            # 状态
            if alert_high and price >= alert_high:
                status = "🔴 突破"
            elif alert_low and price <= alert_low:
                status = "🟢 跌破"
            elif change >= 5:
                status = "🚀 大涨"
            elif change <= -5:
                status = "📉 大跌"
            elif change > 0:
                status = "📈 上涨"
            else:
                status = "📉 下跌"
            
            change_str = f"{change:+.2f}%"
            
            print(f"{name}({symbol})", end=' ')
            print(f"{price:>10.2f} {change_str:>10} {alert_range:>20} {status:<10}")
        
        print("=" * 70)
    
    def run_monitor(self):
        """运行监控"""
        print(f"\n{'='*70}")
        print("🎯 股票盯盘系统")
        print(f"监控股票：{len(WATCH_LIST)} 只")
        if self.discord_webhook:
            print("Discord 通知：✓ 已启用")
        else:
            print("Discord 通知：✗ 未配置")
        print(f"{'='*70}\n")
        
        # 获取价格
        prices = self.get_latest_prices()
        
        # 显示面板
        self.display_dashboard(prices)
        
        # 检查告警
        alerts = self.check_alerts(prices)
        
        if alerts:
            print("\n⚠️  告警触发:")
            for alert in alerts:
                print(f"   {alert['message']}")
                # 发送 Discord 通知
                self.send_discord_notification(alert['message'], alert['type'])
            
            # 存储告警
            conn = sqlite3.connect(self.db_path)
            for alert in alerts:
                conn.execute('''
                    INSERT INTO monitor_alerts (symbol, alert_type, price, threshold, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (alert['symbol'], alert['type'], alert['price'], alert['threshold'], alert['message']))
            conn.commit()
            conn.close()
        else:
            print("\n✅ 无告警触发")
        
        # 显示分析建议
        print("\n📊 今日操作建议:")
        conn = sqlite3.connect(self.db_path)
        for watch in WATCH_LIST:
            symbol = watch['symbol']
            df = pd.read_sql_query('''
                SELECT recommendation, confidence
                FROM comprehensive_analysis
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT 1
            ''', conn, params=(symbol,))
            
            if not df.empty:
                rec = df.iloc[0]['recommendation']
                score = df.iloc[0]['confidence']
                print(f"   {watch['name']}({symbol}): {rec} (评分{score*100:.0f})")
        
        conn.close()
    
    def show_alert_history(self):
        """显示告警历史"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT symbol, alert_type, message, created_at
            FROM monitor_alerts
            ORDER BY created_at DESC
            LIMIT 20
        ''', conn)
        conn.close()
        
        if df.empty:
            print("暂无告警记录")
        else:
            print("\n📋 告警历史:")
            print(df.to_string(index=False))

def continuous_monitor(interval=300, discord_webhook=None):
    """持续监控（默认 5 分钟）"""
    monitor = LocalStockMonitor(discord_webhook=discord_webhook)
    
    print(f"\n{'='*70}")
    print("🎯 股票盯盘系统 - 持续监控模式")
    print(f"监控股票：{len(WATCH_LIST)} 只")
    print(f"刷新间隔：{interval} 秒 ({interval//60}分钟)")
    if discord_webhook:
        print("Discord 通知：✓ 已启用")
    print(f"{'='*70}\n")
    
    try:
        while True:
            monitor.run_monitor()
            print(f"\n⏱️  {interval//60}分钟后刷新... (Ctrl+C 停止)")
            print(f"{'='*70}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n✋ 监控已停止")

if __name__ == "__main__":
    import sys
    
    # 从命令行参数获取 Discord Webhook（可选）
    discord_webhook = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        discord_webhook = sys.argv[1]
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    
    if args and args[0] == "history":
        monitor = LocalStockMonitor()
        monitor.show_alert_history()
    elif args and args[0] == "daemon":
        # 后台持续运行模式
        interval = int(args[1]) if len(args) > 1 else 300
        continuous_monitor(interval, discord_webhook)
    else:
        # 单次运行
        monitor = LocalStockMonitor(discord_webhook=discord_webhook)
        monitor.run_monitor()
