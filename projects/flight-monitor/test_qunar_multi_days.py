"""测试去哪儿多日期价格"""
import requests
import json
import time


def get_qunar_price(dep_code, arr_code, date_str):
    """从去哪儿获取价格"""
    url = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://m.flight.qunar.com',
        'Referer': 'https://m.flight.qunar.com/h5/flight/',
    }
    cookies = {
        'QN1': '000197802f107b496f80bb26',
        'QN48': '000197802f107b496f80bb26',
        'Alina': 'c2440aac-c15f39-944f9e15-838fdb77-28b669b2a7f2',
    }

    flight_code = f"{dep_code}_{arr_code}_{date_str}"
    payload = {
        "b": {
            "timeout": 5000,
            "simpleData": "yes",
            "t": "f_urInfo_superLow_async",
            "flightInfo": [{"flightCode": flight_code, "price": "", "jumpUrl": ""}]
        }
    }

    try:
        resp = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('data', {}).get('asyncResultMap', {}).get(flight_code, {})
            price = result.get('price', '')
            return int(price) if price else None
    except Exception as e:
        print(f"  错误: {e}")
    return None


if __name__ == "__main__":
    print("=== 去哪儿多日期价格测试 ===\n")

    dates = [
        "2026-03-13",
        "2026-03-14",
        "2026-03-15",
        "2026-03-16",
        "2026-03-17",
        "2026-03-18",
        "2026-03-19",
        "2026-03-20",
    ]

    results = []
    for date in dates:
        print(f"查询 {date}...", end=" ")
        price = get_qunar_price("CAN", "TAO", date)
        if price:
            print(f"¥{price}")
            results.append((date, price))
        else:
            print("无数据")
        time.sleep(1)

    print("\n=== 结果汇总 ===")
    print("日期        价格")
    print("-" * 20)
    for date, price in results:
        print(f"{date}  ¥{price}")

    # 检查是否所有价格相同
    prices = [p for _, p in results]
    if len(set(prices)) == 1:
        print(f"\n⚠️  所有日期价格相同: ¥{prices[0]} (静态数据)")
    else:
        print(f"\n✓ 价格有变化: {min(prices)} - {max(prices)} (动态数据)")
