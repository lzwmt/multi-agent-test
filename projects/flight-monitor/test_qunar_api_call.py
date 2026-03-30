"""直接调用去哪儿 H5 API"""
import requests
import json
import time
import random

# H5 API 端点
LOW_PRICE_API = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"
PRICE_CALENDAR_API = "https://gw.flight.qunar.com/api/f/priceCalendar"

# 请求头（模拟 iPhone）
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/javascript, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://m.flight.qunar.com/',
    'X-Requested-With': 'XMLHttpRequest',
}

# Cookie
cookies = {
    '_i': 'DFiEZCOjLGiAUHPL_CeRItNt5MAw',
    '_q': 'U.uslsuus1942',
    '_s': 's_MU6GVX5WXLHZZVXCE22PLRDX7A',
    '_t': '29664446',
    '_v': 'WmNyo_iK8V1KVfy4mzpu3YZvOW7LhqMML7i4SyKLnmWOfk6XWZg_8BtrEbhBqYvF7b-wnYMgjnh9cVEp8IIpkKqGGRPVxQfZ-2gP1uAKKJGdow9hldmpSTExu_t1_Zhv2pcv_k7nqs5xAYe_lMbcd0XcVadY2S2BYTEpyapaV6bF',
    'csrfToken': 'HySpnjeJLVxoFFpcnIlvOIHnJNbxHhGc',
    'fid': 'b1c59615-0d7a-496c-abf8-838a0a4321b4',
}


def call_low_price_api(dep_code: str, arr_code: str, date: str):
    """调用低价接口"""
    print(f"\n{'='*70}")
    print(f"低价接口: {dep_code} -> {arr_code}, 日期: {date}")
    print('='*70)
    
    params = {
        'depCity': dep_code,
        'arrCity': arr_code,
        'depDate': date,
        'type': '1',  # 单程
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        
        resp = requests.get(
            LOW_PRICE_API,
            headers=headers,
            cookies=cookies,
            params=params,
            timeout=30,
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        # 尝试解析 JSON
        try:
            data = resp.json()
            print(f"响应类型: JSON")
            
            # 保存响应
            with open(f'/tmp/qunar_lowprice_{date}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 数据已保存到 /tmp/qunar_lowprice_{date}.json")
            
            # 查找价格
            data_str = json.dumps(data)
            prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', data_str)
            if prices:
                unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                print(f"✓ 找到价格: {unique_prices[:15]}")
                return unique_prices
            else:
                print("⚠ 未找到价格")
                # 打印部分响应
                print(f"响应预览: {json.dumps(data, ensure_ascii=False)[:300]}")
        
        except Exception as e:
            print(f"✗ 解析失败: {e}")
            print(f"响应: {resp.text[:300]}")
    
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    return []


def call_price_calendar_api(dep: str, arr: str):
    """调用价格日历接口"""
    print(f"\n{'='*70}")
    print(f"价格日历: {dep} -> {arr}")
    print('='*70)
    
    params = {
        'dep': dep,
        'arr': arr,
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        
        resp = requests.get(
            PRICE_CALENDAR_API,
            headers=headers,
            cookies=cookies,
            params=params,
            timeout=30,
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        # 尝试解析 JSON
        try:
            data = resp.json()
            print(f"响应类型: JSON")
            
            # 保存响应
            with open('/tmp/qunar_calendar.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 数据已保存到 /tmp/qunar_calendar.json")
            
            # 查找价格
            data_str = json.dumps(data)
            prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', data_str)
            if prices:
                unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                print(f"✓ 找到价格: {unique_prices[:15]}")
                return unique_prices
            else:
                print("⚠ 未找到价格")
                print(f"响应预览: {json.dumps(data, ensure_ascii=False)[:300]}")
        
        except Exception as e:
            print(f"✗ 解析失败: {e}")
            print(f"响应: {resp.text[:300]}")
    
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 API 直接调用")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    # 测试低价接口
    results = {}
    for date_str in dates:
        prices = call_low_price_api('CAN', 'TAO', date_str)
        results[date_str] = prices
    
    # 测试价格日历接口
    call_price_calendar_api('广州', '青岛')
    
    # 对比结果
    print("\n" + "=" * 70)
    print("低价接口结果对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices[:10]}")
        else:
            print(f"{date_str}: 无数据")
