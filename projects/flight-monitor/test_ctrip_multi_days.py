"""测试携程多日期价格"""
import requests
import json
import time
import random


def get_ctrip_price(dep_code, arr_code, date_str):
    """从携程获取价格"""
    url = "https://flights.ctrip.com/international/search/api/search/batchSearch"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://flights.ctrip.com',
        'Referer': 'https://flights.ctrip.com/online/list/round-can-tao',
    }

    cookies = {
        '_bfa': '1.1773298447354.d448XhhHBfUO.1.1773298537519.1773298553036.1.10.102001',
        'GUID': '09031036416118655147',
        'cticket': '05ADD5CC9E616FF981FDAF4AC031B5C1CA4E7BB33775BBBAF8156059A9DE675D',
        'UBT_VID': '1773298447354.d448XhhHBfUO',
        '_RGUID': '4e3823cf-2bda-476c-8658-0c6b5a12cda2',
    }

    payload = {
        "transactionID": f"{int(time.time()*1000)}_can-tao_{random.randint(1000,9999)}",
        "resourceVersion": "2026.03.14.13",
        "flightSegments": [
            {
                "departureAirportCode": dep_code,
                "arrivalAirportCode": arr_code,
                "departureDate": date_str
            }
        ],
        "cabinClass": "Y",
        "adult": 1,
        "child": 0,
        "infant": 0
    }

    try:
        resp = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                flights = data['data'].get('flightItineraryList', [])
                prices = []
                for flight in flights:
                    segments = flight.get('flightSegments', [])
                    if segments:
                        segment = segments[0]
                        if segment.get('transferCount', 0) == 0:
                            price_list = flight.get('priceList', [])
                            if price_list:
                                price = price_list[0].get('adultPrice', 0)
                                if price > 0 and price not in [1000, 2000, 5000]:
                                    prices.append(price)

                if prices:
                    return min(prices)
    except Exception as e:
        print(f"  错误: {e}")
    return None


if __name__ == "__main__":
    print("=== 携程多日期价格测试 ===\n")

    dates = [
        "2026-03-13",
        "2026-03-14",
        "2026-03-15",
        "2026-03-16",
        "2026-03-17",
        "2026-03-18",
    ]

    results = []
    for date in dates:
        print(f"查询 {date}...", end=" ")
        price = get_ctrip_price("CAN", "TAO", date)
        if price:
            print(f"¥{price}")
            results.append((date, price))
        else:
            print("无数据")
        time.sleep(2)

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
