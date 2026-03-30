#!/usr/bin/env python3
"""
AI预测准确率统计系统
追踪预测结果，计算准确率
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

class PredictionAccuracyTracker:
    """预测准确率追踪器"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_tables()
    
    def init_tables(self):
        """初始化准确率统计表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 预测准确率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                predict_date TEXT,          -- 预测日期
                predicted_price REAL,       -- 预测价格
                actual_price REAL,          -- 实际价格
                predicted_change_pct REAL,  -- 预测涨跌%
                actual_change_pct REAL,     -- 实际涨跌%
                direction_correct BOOLEAN,  -- 方向是否正确
                error_pct REAL,             -- 误差百分比
                is_recorded BOOLEAN DEFAULT 0, -- 是否已记录实际值
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accuracy_symbol ON prediction_accuracy(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accuracy_date ON prediction_accuracy(predict_date)')
        
        conn.commit()
        conn.close()
        print("预测准确率表初始化完成")
    
    def record_prediction(self, symbol, predicted_price, predicted_change_pct):
        """记录预测结果"""
        predict_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO prediction_accuracy 
            (symbol, predict_date, predicted_price, predicted_change_pct)
            VALUES (?, ?, ?, ?)
        ''', (symbol, predict_date, predicted_price, predicted_change_pct))
        conn.commit()
        conn.close()
        
        print(f"记录预测: {symbol} {predict_date} 预测价¥{predicted_price:.2f}")
    
    def update_actual_price(self, symbol, predict_date, actual_price, actual_change_pct):
        """更新实际价格（次日）"""
        # 计算方向是否正确
        predicted = self.get_prediction(symbol, predict_date)
        if not predicted:
            print(f"未找到预测记录: {symbol} {predict_date}")
            return
        
        predicted_price = predicted['predicted_price']
        predicted_change = predicted['predicted_change_pct']
        
        # 方向判断
        direction_correct = (predicted_change > 0 and actual_change_pct > 0) or \
                           (predicted_change < 0 and actual_change_pct < 0) or \
                           (abs(predicted_change) < 0.5 and abs(actual_change_pct) < 0.5)
        
        # 误差计算
        error_pct = abs(predicted_change - actual_change_pct)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE prediction_accuracy 
            SET actual_price = ?,
                actual_change_pct = ?,
                direction_correct = ?,
                error_pct = ?,
                is_recorded = 1
            WHERE symbol = ? AND predict_date = ?
        ''', (actual_price, actual_change_pct, direction_correct, error_pct, symbol, predict_date))
        conn.commit()
        conn.close()
        
        print(f"更新实际: {symbol} {predict_date} 实际¥{actual_price:.2f} 方向{'✓' if direction_correct else '✗'} 误差{error_pct:.2f}%")
    
    def get_prediction(self, symbol, predict_date):
        """获取预测记录"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM prediction_accuracy
            WHERE symbol = ? AND predict_date = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', conn, params=(symbol, predict_date))
        conn.close()
        
        if df.empty:
            return None
        return df.iloc[0].to_dict()
    
    def calculate_accuracy(self, symbol=None, days=30):
        """计算准确率统计"""
        conn = sqlite3.connect(self.db_path)
        
        if symbol:
            # 单只股票统计
            df = pd.read_sql_query('''
                SELECT * FROM prediction_accuracy
                WHERE symbol = ? AND is_recorded = 1
                AND predict_date >= date('now', '-{} days')
                ORDER BY predict_date DESC
            '''.format(days), conn, params=(symbol,))
        else:
            # 全部统计
            df = pd.read_sql_query('''
                SELECT * FROM prediction_accuracy
                WHERE is_recorded = 1
                AND predict_date >= date('now', '-{} days')
                ORDER BY predict_date DESC
            '''.format(days), conn)
        
        conn.close()
        
        if df.empty:
            return None
        
        # 计算指标
        total = len(df)
        direction_correct = df['direction_correct'].sum()
        direction_accuracy = direction_correct / total * 100 if total > 0 else 0
        
        avg_error = df['error_pct'].mean()
        
        # 涨跌预测统计
        up_predictions = df[df['predicted_change_pct'] > 0]
        down_predictions = df[df['predicted_change_pct'] < 0]
        
        up_correct = up_predictions['direction_correct'].sum() if len(up_predictions) > 0 else 0
        up_accuracy = up_correct / len(up_predictions) * 100 if len(up_predictions) > 0 else 0
        
        down_correct = down_predictions['direction_correct'].sum() if len(down_predictions) > 0 else 0
        down_accuracy = down_correct / len(down_predictions) * 100 if len(down_predictions) > 0 else 0
        
        return {
            'total': total,
            'direction_accuracy': direction_accuracy,
            'avg_error_pct': avg_error,
            'up_predictions': len(up_predictions),
            'up_accuracy': up_accuracy,
            'down_predictions': len(down_predictions),
            'down_accuracy': down_accuracy,
            'details': df
        }
    
    def generate_accuracy_report(self):
        """生成准确率报告"""
        print("=" * 60)
        print("🎯 AI预测准确率报告")
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        # 总体统计
        overall = self.calculate_accuracy(days=30)
        if overall:
            print(f"\n📊 总体统计（最近30天）:")
            print(f"  总预测次数: {overall['total']}")
            print(f"  方向准确率: {overall['direction_accuracy']:.1f}%")
            print(f"  平均误差: {overall['avg_error_pct']:.2f}%")
            print(f"  上涨预测: {overall['up_predictions']}次，准确率{overall['up_accuracy']:.1f}%")
            print(f"  下跌预测: {overall['down_predictions']}次，准确率{overall['down_accuracy']:.1f}%")
        
        # 单只股票统计
        print(f"\n📈 单只股票统计:")
        stocks = ['600104', '600150', '600326', '600581', '603577', '600410']
        for symbol in stocks:
            stats = self.calculate_accuracy(symbol, days=30)
            if stats and stats['total'] > 0:
                print(f"  {symbol}: 预测{stats['total']}次，方向准确率{stats['direction_accuracy']:.1f}%，平均误差{stats['avg_error_pct']:.2f}%")
        
        print("=" * 60)
    
    def auto_update_actual_prices(self):
        """自动更新昨日预测的实际价格（收盘后15:30更新）"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        
        # 获取昨日未更新的预测
        df = pd.read_sql_query('''
            SELECT symbol, predict_date, predicted_price
            FROM prediction_accuracy
            WHERE predict_date = ? AND is_recorded = 0
        ''', conn, params=(yesterday,))
        
        conn.close()
        
        if df.empty:
            print(f"没有需要更新的预测记录")
            return
        
        print(f"更新 {len(df)} 条预测记录的实际价格...")
        
        # 获取实际价格
        for _, row in df.iterrows():
            symbol = row['symbol']
            
            # 从数据库获取实际价格
            conn = sqlite3.connect(self.db_path)
            actual_df = pd.read_sql_query('''
                SELECT close, change_pct
                FROM stock_prices
                WHERE symbol = ? AND date = ?
            ''', conn, params=(symbol, yesterday))
            conn.close()
            
            if not actual_df.empty:
                actual_price = actual_df.iloc[0]['close']
                actual_change = actual_df.iloc[0]['change_pct']
                self.update_actual_price(symbol, yesterday, actual_price, actual_change)

if __name__ == "__main__":
    import sys
    
    tracker = PredictionAccuracyTracker()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            tracker.generate_accuracy_report()
        elif sys.argv[1] == "update":
            tracker.auto_update_actual_prices()
        else:
            print("用法: python3 prediction_accuracy.py [report|update]")
    else:
        tracker.generate_accuracy_report()
