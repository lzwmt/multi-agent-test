#!/usr/bin/env python3
"""
股票系统资源监控
监控内存、磁盘、数据库大小
"""

import sqlite3
import os
import psutil
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

def get_db_size():
    """获取数据库大小"""
    size = os.path.getsize(DB_PATH)
    return size / (1024 * 1024)  # MB

def get_db_stats():
    """获取数据库统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # 各表记录数
    tables = ['stock_prices', 'stock_minutes', 'stock_indicators', 
              'trading_signals', 'monitor_alerts', 'agent_tasks']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        except:
            stats[table] = 0
    
    conn.close()
    return stats

def check_resources():
    """检查系统资源"""
    # 内存
    mem = psutil.virtual_memory()
    mem_used = mem.used / (1024 * 1024 * 1024)  # GB
    mem_total = mem.total / (1024 * 1024 * 1024)  # GB
    mem_percent = mem.percent
    
    # 磁盘
    disk = psutil.disk_usage('/')
    disk_used = disk.used / (1024 * 1024 * 1024)  # GB
    disk_total = disk.total / (1024 * 1024 * 1024)  # GB
    disk_percent = disk.percent
    
    # 数据库
    db_size = get_db_size()
    db_stats = get_db_stats()
    
    # 打印报告
    print("=" * 60)
    print(f"📊 股票系统资源监控报告")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print(f"\n💾 内存使用:")
    print(f"  已用: {mem_used:.1f} GB / {mem_total:.1f} GB ({mem_percent}%)")
    if mem_percent > 80:
        print(f"  ⚠️  警告: 内存使用率过高！")
    elif mem_percent > 60:
        print(f"  ⚡ 注意: 内存使用率偏高")
    else:
        print(f"  ✅ 内存使用正常")
    
    print(f"\n💿 磁盘使用:")
    print(f"  已用: {disk_used:.1f} GB / {disk_total:.1f} GB ({disk_percent}%)")
    if disk_percent > 90:
        print(f"  ⚠️  警告: 磁盘空间不足！")
    elif disk_percent > 70:
        print(f"  ⚡ 注意: 磁盘空间偏低")
    else:
        print(f"  ✅ 磁盘空间充足")
    
    print(f"\n🗄️  数据库:")
    print(f"  大小: {db_size:.1f} MB")
    print(f"\n  表记录数:")
    for table, count in db_stats.items():
        print(f"    {table}: {count:,} 条")
    
    # 建议
    print(f"\n📋 优化建议:")
    if db_size > 500:
        print(f"  • 数据库较大，建议运行: python3 stock_data_cleanup.py")
    if mem_percent > 70:
        print(f"  • 内存使用率较高，建议减少监控股票数量")
    if disk_percent > 80:
        print(f"  • 磁盘空间紧张，建议清理日志文件")
    
    print("=" * 60)
    
    return {
        'mem_percent': mem_percent,
        'disk_percent': disk_percent,
        'db_size_mb': db_size,
        'db_stats': db_stats
    }

if __name__ == "__main__":
    check_resources()
