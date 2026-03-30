#!/usr/bin/env python3
"""将抓取的数据写入飞书多维表格"""
import json
import sys

# 飞书表格配置
BITABLE_APP_TOKEN = "YgZlbTL1kaCxhjsc0TgcfdO7ned"
BITABLE_TABLE_ID = "tbl9EwlPHmYhl0FP"

def write_to_bitable(records_file: str):
    """读取记录文件并写入飞书表格"""
    
    # 读取记录
    with open(records_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get('records', [])
    print(f"准备写入 {len(records)} 条记录到飞书表格")
    
    # 分批写入，每批 100 条（API 限制）
    batch_size = 100
    total_saved = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        # 使用 feishu_bitable_app_table_record 工具
        from feishu_bitable_app_table_record import feishu_bitable_app_table_record
        
        result = feishu_bitable_app_table_record(
            action="batch_create",
            app_token=BITABLE_APP_TOKEN,
            table_id=BITABLE_TABLE_ID,
            records=batch
        )
        
        if result.get('status') == 'success' or 'records' in result:
            saved_count = len(result.get('records', batch))
            total_saved += saved_count
            print(f"  ✓ 批次 {i//batch_size + 1}: 已保存 {saved_count} 条")
        else:
            print(f"  ✗ 批次 {i//batch_size + 1}: 失败 - {result}")
    
    print(f"\n总计写入: {total_saved}/{len(records)} 条记录")
    return total_saved > 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python write_to_bitable.py <records_file.json>")
        print("示例: python write_to_bitable.py /tmp/flight_records.json")
        sys.exit(1)
    
    records_file = sys.argv[1]
    success = write_to_bitable(records_file)
    sys.exit(0 if success else 1)
