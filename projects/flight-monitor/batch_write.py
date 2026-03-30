#!/usr/bin/env python3
"""批量写入飞书表格"""
import json
import subprocess
import sys

# 配置
APP_TOKEN = "YgZlbTL1kaCxhjsc0TgcfdO7ned"
TABLE_ID = "tbl9EwlPHmYhl0FP"

def write_records(records):
    """写入一批记录"""
    # 构建命令
    records_json = json.dumps(records, ensure_ascii=False)
    
    # 使用 openclaw CLI
    cmd = [
        "openclaw", "feishu", "bitable", "record", "batch-create",
        "--app-token", APP_TOKEN,
        "--table-id", TABLE_ID,
        "--records", records_json
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    # 读取数据
    with open('/tmp/flight_records.json', 'r') as f:
        data = json.load(f)
    
    records = data['records']
    print(f"总共 {len(records)} 条记录")
    
    # 分批写入，每批 10 条
    batch_size = 10
    total_saved = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        print(f"\n写入批次 {i//batch_size + 1}/{(len(records)-1)//batch_size + 1} ({len(batch)} 条)...")
        
        success, stdout, stderr = write_records(batch)
        if success:
            total_saved += len(batch)
            print(f"  ✓ 成功")
        else:
            print(f"  ✗ 失败: {stderr}")
    
    print(f"\n总计写入: {total_saved}/{len(records)} 条记录")
    return 0 if total_saved == len(records) else 1

if __name__ == "__main__":
    sys.exit(main())
