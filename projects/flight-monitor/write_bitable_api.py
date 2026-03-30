#!/usr/bin/env python3
"""批量写入飞书表格 - 使用 API 直接调用"""
import json
import requests
import sys

# 配置
APP_TOKEN = "YgZlbTL1kaCxhjsc0TgcfdO7ned"
TABLE_ID = "tbl9EwlPHmYhl0FP"

def get_access_token():
    """获取飞书 access token"""
    # 从环境变量或配置文件读取
    # 这里需要用户的 access token
    import os
    token = os.environ.get('FEISHU_ACCESS_TOKEN')
    if not token:
        print("错误: 未设置 FEISHU_ACCESS_TOKEN 环境变量")
        print("请运行: export FEISHU_ACCESS_TOKEN=your_token")
        return None
    return token

def write_records_batch(records, access_token):
    """写入一批记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "records": records
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200, response.json()

def main():
    # 读取数据
    with open('/tmp/flight_records.json', 'r') as f:
        data = json.load(f)
    
    records = data['records']
    print(f"总共 {len(records)} 条记录")
    
    # 获取 access token
    access_token = get_access_token()
    if not access_token:
        return 1
    
    # 分批写入，每批 500 条（API 限制）
    batch_size = 500
    total_saved = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        print(f"\n写入批次 {i//batch_size + 1} ({len(batch)} 条)...")
        
        success, result = write_records_batch(batch, access_token)
        if success:
            saved = len(result.get('data', {}).get('records', batch))
            total_saved += saved
            print(f"  ✓ 成功写入 {saved} 条")
        else:
            print(f"  ✗ 失败: {result}")
    
    print(f"\n总计写入: {total_saved}/{len(records)} 条记录")
    return 0 if total_saved == len(records) else 1

if __name__ == "__main__":
    sys.exit(main())
