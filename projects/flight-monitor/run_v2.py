#!/usr/bin/env python3
"""机票价格监控 V2 - 多数据源"""
import sys
import json
from datetime import datetime

from fetcher_v2 import FlightFetcher
from config import ORIGIN_CODE, DESTINATION_CODE, DAYS_AHEAD, PRICE_THRESHOLD


def run_monitor():
    """执行价格监控"""
    print("=" * 60)
    print("机票价格监控 V2")
    print(f"航线：广州 ({ORIGIN_CODE}) → 青岛 ({DESTINATION_CODE})")
    print(f"监控天数：{DAYS_AHEAD}")
    print(f"低价阈值：¥{PRICE_THRESHOLD}")
    print("=" * 60)

    # 抓取数据
    fetcher = FlightFetcher()
    all_flights = fetcher.fetch_multiple_days(ORIGIN_CODE, DESTINATION_CODE, days=min(7, DAYS_AHEAD))

    if not all_flights:
        print("\n❌ 未获取到任何数据")
        return {"status": "error", "message": "no_data"}

    # 统计分析
    print("\n" + "=" * 60)
    print("数据分析")
    print("=" * 60)

    # 按日期分组
    by_date = {}
    for f in all_flights:
        date = f['date']
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(f)

    # 按数据源分组
    by_source = {}
    for f in all_flights:
        source = f['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(f)

    print(f"\n总计：{len(all_flights)} 条价格记录")
    print(f"\n按日期统计:")
    for date in sorted(by_date.keys()):
        flights = by_date[date]
        sources = set(f['source'] for f in flights)
        prices = [f['price'] for f in flights]
        min_price = min(prices)
        print(f"  {date}: {len(flights)}条 | 最低¥{min_price} | 来源: {', '.join(sources)}")

    print(f"\n按数据源统计:")
    for source, flights in by_source.items():
        prices = [f['price'] for f in flights]
        print(f"  {source}: {len(flights)}条 | 价格范围 ¥{min(prices)}-{max(prices)}")

    # 检查低价
    print(f"\n低价提醒 (<= ¥{PRICE_THRESHOLD}):")
    low_prices = [f for f in all_flights if f['price'] <= PRICE_THRESHOLD]
    if low_prices:
        for f in sorted(low_prices, key=lambda x: x['price'])[:10]:
            print(f"  📅 {f['date']}: ¥{f['price']} ({f['source']})")
    else:
        print("  无低价提醒")

    # 保存到文件
    output_file = "/tmp/flight_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "route": f"{ORIGIN_CODE}-{DESTINATION_CODE}",
            "total_records": len(all_flights),
            "flights": all_flights,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 数据已保存: {output_file}")

    return {
        "status": "success",
        "total_records": len(all_flights),
        "by_date": {d: len(v) for d, v in by_date.items()},
        "by_source": {s: len(v) for s, v in by_source.items()},
    }


if __name__ == "__main__":
    result = run_monitor()
    print("\n" + "=" * 60)
    print("监控完成")
    print("=" * 60)
    sys.exit(0 if result["status"] == "success" else 1)
