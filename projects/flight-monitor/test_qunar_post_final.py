"""使用正确格式调用去哪儿 POST 接口"""
import requests
import json
import time
import random

PRICE_API = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"

# 请求头（从拦截获取）
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': '*/*',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://m.flight.qunar.com',
    'Referer': 'https://m.flight.qunar.com/h5/flight/',
}

# Cookie（从拦截获取）
cookies = {
    'QN1': '000197802f107b496f80bb26',
    'QN48': '000197802f107b496f80bb26',
    'QN300': 'organic',
    'AKA_A2': 'A',
    'Alina': 'c2440aac-c15f39-944f9e15-838fdb77-28b669b2a7f2',
}


def call_price_api(dep_code: str, arr_code: str, date: str):
    """调用价格接口"""
    print(f"\n{'='*70}")
    print(f"POST: {dep_code} -> {arr_code}, 日期: {date}")
    print('='*70)
    
    # 构造 flightCode
    flight_code = f"{dep_code}_{arr_code}_{date}"
    
    # 构造 POST 数据
    payload = {
        "b": {
            "timeout": 5000,
            "simpleData": "yes",
            "t": "f_urInfo_superLow_async",
            "flightInfo": [
                {
                    "flightCode": flight_code,
                    "price": "",
                    "jumpUrl": ""
                }
            ]
        }
    }
    
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)[:200]}")
    
    try:
        time.sleep(random.uniform(1, 2))
        
        resp = requests.post(
            PRICE_API,
            headers=headers,
            cookies=cookies,
            json=payload,
            timeout=30,
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        # 尝试解析
        try:
            data = resp.json()
            print(f"✓ JSON 响应")
            
            # 保存
            with open(f'/tmp/qunar_post_final_{date}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 数据已保存")
            
            # 查找价格
            data_str = json.dumps(data)
            prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', data_str)
            if prices:
                unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                print(f"✓ 找到价格: {unique_prices[:15]}")
                return unique_prices
            else:
                print(f"预览: {json.dumps(data, ensure_ascii=False)[:300]}")
        
        except Exception as e:
            print(f"✗ 解析失败: {e}")
            print(f"响应: {resp.text[:300]}")
    
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 POST 接口最终测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    results = {}
    for date_str in dates:
        prices = call_price_api('CAN', 'TAO', date_str)
        results[date_str] = prices
    
    # 对比
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices[:10]}")
        else:
            print(f"{date_str}: 无数据")
