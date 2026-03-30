"""用新鲜Cookie测试携程API"""
import json
import time
import requests


def test_with_fresh_cookies():
    """用新鲜Cookie测试"""
    print("=== 用新鲜Cookie测试携程API ===\n")

    # 读取新鲜Cookie
    with open('/tmp/ctrip_fresh_cookies.json', 'r') as f:
        cookies = json.load(f)

    print(f"使用 {len(cookies)} 个Cookie:\n")
    for name, value in list(cookies.items())[:5]:
        print(f"  {name}: {value[:40]}...")

    # 调用API
    url = "https://flights.ctrip.com/international/search/api/search/batchSearch"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://flights.ctrip.com',
        'Referer': 'https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14',
    }

    payload = {
        "transactionID": f"{int(time.time()*1000)}_can-tao_{int(time.time())}",
        "resourceVersion": "2026.03.14.13",
        "flightSegments": [
            {
                "departureAirportCode": "CAN",
                "arrivalAirportCode": "TAO",
                "departureDate": "2026-03-14"
            }
        ],
        "cabinClass": "Y",
        "adult": 1,
        "child": 0,
        "infant": 0
    }

    print(f"\n调用API...")
    resp = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)

    print(f"状态码: {resp.status_code}")
    print(f"\n响应:\n{resp.text[:1000]}")

    if resp.status_code == 200:
        data = resp.json()
        if data.get('data') and data['data'].get('flightItineraryList'):
            flights = data['data']['flightItineraryList']
            print(f"\n✓ 成功! 返回 {len(flights)} 个航班")

            # 解析
            prices = []
            for flight in flights:
                segments = flight.get('flightSegments', [])
                if segments:
                    segment = segments[0]
                    if segment.get('transferCount', 0) == 0:
                        flight_list = segment.get('flightList', [])
                        if flight_list:
                            price_list = flight.get('priceList', [])
                            if price_list:
                                price = price_list[0].get('adultPrice', 0)
                                if price > 0 and price not in [1000, 2000, 5000]:
                                    prices.append(price)
                                    if len(prices) <= 5:
                                        f = flight_list[0]
                                        print(f"  {f.get('flightNo')}: ¥{price}")

            if prices:
                print(f"\n最低价格: ¥{min(prices)}")
        else:
            print(f"\n✗ 无数据: {data.get('errorMessage', '未知错误')}")


if __name__ == "__main__":
    test_with_fresh_cookies()
