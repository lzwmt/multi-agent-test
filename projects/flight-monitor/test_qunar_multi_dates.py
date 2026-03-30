"""去哪儿多日期动态价格测试"""
import requests
import json
import time
import random
from datetime import datetime, timedelta

PRICE_API = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': '*/*',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://m.flight.qunar.com',
    'Referer': 'https://m.flight.qunar.com/h5/flight/',
}

cookies = {
    'QN1': '000197802f107b496f80bb26',
    'QN48': '000197802f107b496f80bb26',
    'Alina': 'c2440aac-c15f39-944f9e15-838fdb77-28b669b2a7f2',
}


def get_price(dep_code: str, arr_code: str, date: str):
    """获取价格"""
    flight_code = f"{dep_code}_{arr_code}_{date}"
    
    payload = {
        "b": {
            "timeout": 5000,
            "simpleData": "yes",
            "t": "f_urInfo_superLow_async",
            "flightInfo": [{"flightCode": flight_code, "price": "", "jumpUrl": ""}]
        }
    }
    
    try:
        time.sleep(random.uniform(0.5, 1.5))
        
        resp = requests.post(
            PRICE_API,
            headers=headers,
            cookies=cookies,
            json=payload,
            timeout=30,
        )
        
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('data', {}).get('asyncResultMap', {}).get(flight_code, {})
            price = result.get('price', '')
            if price:
                return int(price)
        
        return None
    
    except Exception as e:
        print(f"  ✗ {date}: {e}")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿多日期动态价格测试")
    print("=" * 70)
    
    # 生成未来 14 天的日期
    base_date = datetime(2026, 3, 12)
    dates = [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
    
    print(f"\n测试日期: {dates[0]} 到 {dates[-1]}")
    print(f"航线: 广州(CAN) -> 青岛(TAO)")
    print("-" * 70)
    
    results = []
    for date_str in dates:
        price = get_price('CAN', 'TAO', date_str)
        results.append({'date': date_str, 'price': price})
        
        if price:
            print(f"{date_str}: ¥{price}")
        else:
            print(f"{date_str}: 无数据")
    
    # 统计
    print("\n" + "=" * 70)
    print("价格统计")
    print("=" * 70)
    
    prices = [r['price'] for r in results if r['price']]
    if prices:
        print(f"最低价格: ¥{min(prices)}")
        print(f"最高价格: ¥{max(prices)}")
        print(f"平均价格: ¥{sum(prices)//len(prices)}")
        
        # 找出最低价的日期
        min_price = min(prices)
        best_dates = [r['date'] for r in results if r['price'] == min_price]
        print(f"最低价日期: {', '.join(best_dates)}")
    
    # 保存结果
    with open('/tmp/qunar_prices.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 结果已保存到 /tmp/qunar_prices.json")
