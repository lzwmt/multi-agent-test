#!/usr/bin/env python3
"""
股票数据清理工具
自动删除过期数据，释放空间
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

def clean_old_data():
    """清理过期数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 清理超过90天的分钟数据
    cutoff_minute = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    cursor.execute("""
        DELETE FROM stock_minutes 
        WHERE datetime < ?
    """, (cutoff_minute,))
    minute_deleted = cursor.rowcount
    
    # 2. 清理超过2年的历史数据（保留最近2年）
    cutoff_daily = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    cursor.execute("""
        DELETE FROM stock_prices 
        WHERE date < ?
    """, (cutoff_daily,))
    daily_deleted = cursor.rowcount
    
    # 3. 清理超过30天的告警记录
    cutoff_alert = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute("""
        DELETE FROM monitor_alerts 
        WHERE date(created_at) < ?
    """, (cutoff_alert,))
    alert_deleted = cursor.rowcount
    
    # 4. 清理超过7天的任务日志
    cutoff_task = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute("""
        DELETE FROM agent_tasks 
        WHERE date(created_at) < ?
    """, (cutoff_task,))
    task_deleted = cursor.rowcount
    
    # 5. 清理超过30天的预测记录
    cutoff_pred = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute("""
        DELETE FROM price_predictions 
        WHERE date(prediction_date) < ?
    """, (cutoff_pred,))
    pred_deleted = cursor.rowcount
    
    conn.commit()
    
    # 执行VACUUM释放空间
    cursor.execute("VACUUM")
    conn.close()
    
    # 获取清理后大小
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB
    
    print(f"数据清理完成:")
    print(f"  分钟数据: 删除 {minute_deleted} 条")
    print(f"  日线数据: 删除 {daily_deleted} 条")
    print(f"  告警记录: 删除 {alert_deleted} 条")
    print(f"  任务日志: 删除 {task_deleted} 条")
    print(f"  预测记录: 删除 {pred_deleted} 条")
    print(f"  数据库大小: {db_size:.1f} MB")
    
    return {
        'minute_deleted': minute_deleted,
        'daily_deleted': daily_deleted,
        'alert_deleted': alert_deleted,
        'task_deleted': task_deleted,
        'pred_deleted': pred_deleted,
        'db_size_mb': db_size
    }

if __name__ == "__main__":
    clean_old_data()
