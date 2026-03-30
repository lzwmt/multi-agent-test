#!/usr/bin/env python3
"""
股票分析 Agent
异步处理股票数据更新、分析和预测
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import sys
import os

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

STOCKS = {
    '600104': '上汽集团',
    '600150': '中国船舶',
    '600326': '西藏天路',
    '600581': '八一钢铁',
    '603577': '汇金通',
}

class StockAgent:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_tables()
    
    def init_tables(self):
        """初始化数据表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 任务日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                symbol TEXT,
                status TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_task(self, task_type, symbol, status, message=""):
        """记录任务日志"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO agent_tasks (task_type, symbol, status, message)
            VALUES (?, ?, ?, ?)
        ''', (task_type, symbol, status, message))
        conn.commit()
        conn.close()
    
    def update_daily_data(self, symbol, name):
        """更新日线数据"""
        try:
            self.log_task("UPDATE_DAILY", symbol, "RUNNING", f"开始更新{name}")
            
            # 获取最近90天数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=symbol, period='daily', 
                                   start_date=start_date, end_date=end_date)
            
            if df.empty:
                self.log_task("UPDATE_DAILY", symbol, "FAILED", "无数据")
                return False
            
            # 处理数据
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high',
                '最低': 'low', '成交量': 'volume', '成交额': 'amount',
                '振幅': 'amplitude', '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount', '换手率': 'turnover'
            })
            df['symbol'] = symbol
            
            columns = ['symbol', 'date', 'open', 'close', 'high', 'low', 'volume',
                      'amount', 'amplitude', 'change_pct', 'change_amount', 'turnover']
            df = df[columns]
            
            # 存储数据
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stock_prices WHERE symbol = ?', (symbol,))
            conn.commit()
            df.to_sql('stock_prices', conn, if_exists='append', index=False)
            conn.close()
            
            self.log_task("UPDATE_DAILY", symbol, "SUCCESS", f"更新{len(df)}条")
            return True
            
        except Exception as e:
            self.log_task("UPDATE_DAILY", symbol, "ERROR", str(e)[:100])
            return False
    
    def calculate_indicators(self, symbol):
        """计算技术指标"""
        try:
            self.log_task("CALC_INDICATORS", symbol, "RUNNING")
            
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
                conn, params=(symbol,)
            )
            
            if len(df) < 30:
                conn.close()
                self.log_task("CALC_INDICATORS", symbol, "FAILED", "数据不足")
                return False
            
            # 计算指标
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma10'] = df['close'].rolling(10).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['rsi6'] = 100 - (100 / (1 + gain / loss))
            
            # MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['macd_dif'] = ema12 - ema26
            df['macd_dea'] = df['macd_dif'].ewm(span=9).mean()
            df['macd_bar'] = (df['macd_dif'] - df['macd_dea']) * 2
            
            # 布林带
            df['boll_mid'] = df['close'].rolling(20).mean()
            std = df['close'].rolling(20).std()
            df['boll_upper'] = df['boll_mid'] + std * 2
            df['boll_lower'] = df['boll_mid'] - std * 2
            
            # 波动率
            df['volatility'] = df['close'].pct_change().rolling(20).std() * 100
            
            # 存储指标
            indicator_cols = ['symbol', 'date', 'close', 'volume', 'ma5', 'ma10', 'ma20',
                            'rsi6', 'macd_dif', 'macd_dea', 'macd_bar',
                            'boll_upper', 'boll_mid', 'boll_lower', 'volatility']
            
            indicators_df = df[indicator_cols].dropna()
            
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stock_indicators WHERE symbol = ?', (symbol,))
            conn.commit()
            
            indicators_df.to_sql('stock_indicators', conn, if_exists='append', index=False)
            conn.close()
            
            self.log_task("CALC_INDICATORS", symbol, "SUCCESS", f"{len(indicators_df)}条")
            return True
            
        except Exception as e:
            self.log_task("CALC_INDICATORS", symbol, "ERROR", str(e)[:100])
            return False
    
    def generate_signals(self, symbol):
        """生成交易信号"""
        try:
            self.log_task("GEN_SIGNALS", symbol, "RUNNING")
            
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM stock_indicators WHERE symbol = ? ORDER BY date",
                conn, params=(symbol,)
            )
            
            if len(df) < 2:
                conn.close()
                return False
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            signals = []
            
            # MACD金叉/死叉
            if prev['macd_dif'] < prev['macd_dea'] and latest['macd_dif'] > latest['macd_dea']:
                signals.append(('MACD_GOLDEN_CROSS', 'MACD金叉，买入信号', 0.7, latest['close']))
            elif prev['macd_dif'] > prev['macd_dea'] and latest['macd_dif'] < latest['macd_dea']:
                signals.append(('MACD_DEATH_CROSS', 'MACD死叉，卖出信号', 0.7, latest['close']))
            
            # RSI超买/超卖
            if latest['rsi6'] < 30:
                signals.append(('RSI_OVERSOLD', f'RSI超卖({latest["rsi6"]:.0f})，可能反弹', 0.6, latest['close']))
            elif latest['rsi6'] > 70:
                signals.append(('RSI_OVERBOUGHT', f'RSI超买({latest["rsi6"]:.0f})，可能回调', 0.6, latest['close']))
            
            # 存储信号
            cursor = conn.cursor()
            cursor.execute('DELETE FROM trading_signals WHERE symbol = ? AND date = ?',
                         (symbol, latest['date']))
            conn.commit()
            
            for sig in signals:
                conn.execute('''
                    INSERT INTO trading_signals (symbol, date, signal_type, signal_desc, confidence, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (symbol, latest['date'], sig[0], sig[1], sig[2], sig[3]))
            
            conn.commit()
            conn.close()
            
            self.log_task("GEN_SIGNALS", symbol, "SUCCESS", f"{len(signals)}个信号")
            return True
            
        except Exception as e:
            self.log_task("GEN_SIGNALS", symbol, "ERROR", str(e)[:100])
            return False
    
    def run_full_analysis(self):
        """运行完整分析"""
        print(f"[{datetime.now()}] Agent 开始运行...")
        
        for symbol, name in STOCKS.items():
            print(f"\n处理 {name}({symbol})...")
            
            # 1. 更新数据
            if self.update_daily_data(symbol, name):
                print("  ✓ 数据更新")
                
                # 2. 计算指标
                if self.calculate_indicators(symbol):
                    print("  ✓ 指标计算")
                    
                    # 3. 生成信号
                    if self.generate_signals(symbol):
                        print("  ✓ 信号生成")
                    else:
                        print("  ✗ 信号失败")
                else:
                    print("  ✗ 指标失败")
            else:
                print("  ✗ 数据失败")
        
        print(f"\n[{datetime.now()}] Agent 完成")
    
    def get_status(self):
        """获取Agent状态"""
        conn = sqlite3.connect(self.db_path)
        
        # 最新任务
        tasks = pd.read_sql_query('''
            SELECT task_type, symbol, status, message, created_at
            FROM agent_tasks
            ORDER BY created_at DESC
            LIMIT 10
        ''', conn)
        
        # 统计
        stats = pd.read_sql_query('''
            SELECT task_type, status, COUNT(*) as count
            FROM agent_tasks
            WHERE created_at >= date('now', '-1 day')
            GROUP BY task_type, status
        ''', conn)
        
        conn.close()
        
        print("=" * 50)
        print("Agent 状态")
        print("=" * 50)
        print("\n最近任务:")
        print(tasks.to_string(index=False))
        print("\n今日统计:")
        print(stats.to_string(index=False))

if __name__ == "__main__":
    agent = StockAgent()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            agent.get_status()
        elif sys.argv[1] == "run":
            agent.run_full_analysis()
        else:
            print("用法: python3 stock_agent.py [run|status]")
    else:
        agent.run_full_analysis()
