#!/usr/bin/env python3
"""机票价格监控 - 完整版本（含飞书存储 + Discord 通知）"""
import sys
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ORIGIN_CODE, DESTINATION_CODE, DAYS_AHEAD, PRICE_THRESHOLD
from fetcher_v2 import FlightFetcher
from storage import format_flight_records, check_price_alert
from notifier import format_price_alert_message, format_daily_report

# 飞书多维表格配置
BITABLE_APP_TOKEN = "YgZlbTL1kaCxhjsc0TgcfdO7ned"
BITABLE_TABLE_ID = "tbl9EwlPHmYhl0FP"

# SGD 转 CNY 汇率
SGD_TO_CNY = 5.4


def save_to_bitable(records: List[Dict]) -> bool:
    """保存记录到飞书多维表格 - 使用工具直接写入"""
    try:
        from feishu_bitable_tool import batch_create_records
        
        print(f"准备保存 {len(records)} 条记录到飞书表格")
        
        # 转换记录格式
        bitable_records = []
        for r in records:
            bitable_records.append({
                "fields": {
                    "日期": r['日期'],
                    "价格": r['价格'],
                    "货币": r.get('货币', 'CNY'),
                    "数据源": r.get('数据源', '未知'),
                    "航线": r.get('航线', '广州-青岛'),
                    "抓取时间": r.get('抓取时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                }
            })
        
        # 使用工具写入飞书
        success = batch_create_records(BITABLE_APP_TOKEN, BITABLE_TABLE_ID, bitable_records)
        
        if success:
            print(f"✓ 成功保存 {len(bitable_records)} 条记录")
        else:
            print(f"✗ 保存失败")
        
        return success
        
    except Exception as e:
        print(f"保存失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def send_discord_message(message: str) -> bool:
    """发送 Discord 消息 - 使用工具直接发送"""
    try:
        # 尝试使用 message 工具发送
        try:
            from message_tool import send_message
            send_message(channel="#main", message=message)
            return True
        except ImportError:
            # 回退到打印模式
            print("DISCORD_MESSAGE:")
            print(json.dumps({
                "channel": "#main",
                "message": message
            }, ensure_ascii=False, indent=2))
            return True
    except Exception as e:
        print(f"发送失败：{e}")
        return False


def run_monitor() -> Dict:
    """执行价格监控"""
    print("=" * 50)
    print("机票价格监控启动")
    print(f"航线：广州 ({ORIGIN_CODE}) → 青岛 ({DESTINATION_CODE})")
    print(f"监控天数：{DAYS_AHEAD}")
    print(f"低价阈值：¥{PRICE_THRESHOLD}")
    print("=" * 50)

    # 1. 抓取数据
    print("\n[1/5] 开始抓取价格数据...")
    fetcher = FlightFetcher()

    # 使用新的多数据源抓取
    all_flights = fetcher.fetch_multiple_days(ORIGIN_CODE, DESTINATION_CODE, days=min(7, DAYS_AHEAD))

    print(f"\n总计抓取：{len(all_flights)} 条价格记录")

    if not all_flights:
        print("❌ 未获取到任何数据，监控结束")
        return {"status": "error", "message": "no_data"}

    # 2. 格式化数据
    print("\n[2/5] 格式化数据...")
    records = format_flight_records(all_flights)

    # 3. 保存到飞书表格
    print("\n[3/5] 保存数据到飞书表格...")
    save_to_bitable(records)

    # 4. 检查低价提醒
    print("\n[4/5] 检查低价提醒...")
    
    # 按数据源分组统计
    by_source = {}
    for r in records:
        source = r.get('数据源', '未知')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(r)
    
    print(f"\n数据源统计:")
    for source, items in by_source.items():
        prices = [item['价格'] for item in items]
        print(f"  {source}: {len(items)}条, 价格范围 ¥{min(prices)}-{max(prices)}")
    
    alerts = check_price_alert(records, threshold=PRICE_THRESHOLD)
    print(f"\n发现 {len(alerts)} 个低于 ¥{PRICE_THRESHOLD} 的价格")

    for alert in alerts:
        print(f"  📅 {alert['日期']}: ¥{alert['price_cny']} ({alert.get('数据源', '未知')})")

    # 5. 发送通知
    print("\n[5/5] 发送通知...")

    result = {
        "status": "success",
        "total_records": len(records),
        "alerts_count": len(alerts),
        "alerts": alerts,
    }

    if alerts:
        alert_msg = format_price_alert_message(alerts)
        send_discord_message(alert_msg)
        result["alert_message"] = alert_msg
    else:
        # 发送每日报告
        report = format_daily_report(records)
        send_discord_message(report)
        result["report"] = report

    print("\n✅ 监控完成")
    return result


def main():
    """主入口"""
    result = run_monitor()
    
    # 输出最终结果
    print("\n" + "=" * 50)
    print("FINAL_RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
