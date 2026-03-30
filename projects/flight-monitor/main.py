"""机票价格监控主程序"""
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict

# 导入配置和模块
from config import (
    ORIGIN_CODE, DESTINATION_CODE,
    DAYS_AHEAD, PRICE_THRESHOLD,
)
from fetcher_v2 import FlightFetcher
from storage import format_flight_records, check_price_alert
from notifier import format_price_alert_message, format_daily_report


def run_monitor(dry_run: bool = False) -> Dict:
    """
    执行价格监控

    Args:
        dry_run: 如果为 True，只抓取数据不发送通知

    Returns:
        执行结果统计
    """
    print("=" * 50)
    print("机票价格监控启动")
    print(f"航线: 广州({ORIGIN_CODE}) → 青岛({DESTINATION_CODE})")
    print(f"监控天数: {DAYS_AHEAD}")
    print(f"低价阈值: ¥{PRICE_THRESHOLD}")
    print("=" * 50)

    # 1. 抓取数据
    print("\n[1/4] 开始抓取价格数据...")
    fetcher = FlightFetcher()

    all_flights = []
    today = datetime.now()

    for i in range(min(DAYS_AHEAD, 7)):  # 先测试7天
        date = today + timedelta(days=i)
        flights = fetcher.fetch_skyscanner(ORIGIN_CODE, DESTINATION_CODE, date)
        if flights:
            all_flights.extend(flights)
            print(f"  ✓ {date.strftime('%Y-%m-%d')}: {len(flights)} 条价格")
        else:
            print(f"  ✗ {date.strftime('%Y-%m-%d')}: 无数据")

    print(f"\n总计抓取: {len(all_flights)} 条价格记录")

    if not all_flights:
        print("❌ 未获取到任何数据，监控结束")
        return {"status": "error", "message": "no_data"}

    # 2. 格式化数据
    print("\n[2/4] 格式化数据...")
    records = format_flight_records(all_flights)

    # 3. 检查低价提醒
    print("\n[3/4] 检查低价提醒...")
    alerts = check_price_alert(records, threshold=PRICE_THRESHOLD)
    print(f"发现 {len(alerts)} 个低于 ¥{PRICE_THRESHOLD} 的价格")

    for alert in alerts:
        print(f"  📅 {alert['date']}: ¥{alert['price_cny']}")

    # 4. 生成通知消息
    print("\n[4/4] 生成通知...")

    result = {
        "status": "success",
        "total_records": len(records),
        "alerts_count": len(alerts),
        "alerts": alerts,
        "report": None,
        "alert_message": None,
    }

    if alerts:
        alert_msg = format_price_alert_message(alerts)
        result["alert_message"] = alert_msg
        print("\n低价提醒消息:")
        print(alert_msg)
    else:
        print("无低价提醒")

    # 生成每日报告
    report = format_daily_report(records)
    result["report"] = report
    print("\n每日报告:")
    print(report)

    # 如果不是 dry_run，返回结果供外部发送通知
    if not dry_run:
        print("\n✅ 监控完成，请查看通知消息")
    else:
        print("\n✅ 测试完成 (dry_run 模式，未发送通知)")

    return result


def main():
    """主入口"""
    # 检查命令行参数
    dry_run = "--dry-run" in sys.argv

    # 运行监控
    result = run_monitor(dry_run=dry_run)

    # 输出 JSON 结果（供外部程序解析）
    print("\n" + "=" * 50)
    print("RESULT_JSON:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
