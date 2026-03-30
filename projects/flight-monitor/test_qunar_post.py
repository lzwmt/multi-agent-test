"""直接调用去哪儿 POST 价格接口"""
import requests
import json
import time
import random

# POST 接口
PRICE_API = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://m.flight.qunar.com/',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://m.flight.qunar.com',
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


def call_price_api(dep_code: str, arr_code: str, date: str):
    """调用价格接口"""
    print(f"\n{'='*70}")
    print(f"POST 价格接口: {dep_code} -> {arr_code}, 日期: {date}")
    print('='*70)
    
    # 构造 POST 数据（尝试不同格式）
    payloads = [
        # 格式1: 表单数据
        {
            'depCity': dep_code,
            'arrCity': arr_code,
            'depDate': date,
            'type': '1',
        },
        # 格式2: JSON
        json.dumps({
            'depCity': dep_code,
            'arrCity': arr_code,
            'depDate': date,
            'type': '1',
        }),
        # 格式3: 带额外参数
        {
            'depCity': dep_code,
            'arrCity': arr_code,
            'depDate': date,
            'type': '1',
            'token': '',
            'sign': '',
        },
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n尝试格式 {i}...")
        
        try:
            time.sleep(random.uniform(1, 2))
            
            if i == 2:
                # JSON 格式
                h = headers.copy()
                h['Content-Type'] = 'application/json'
                resp = requests.post(
                    PRICE_API,
                    headers=h,
                    cookies=cookies,
                    data=payload,
                    timeout=30,
                )
            else:
                # 表单格式
                resp = requests.post(
                    PRICE_API,
                    headers=headers,
                    cookies=cookies,
                    data=payload,
                    timeout=30,
                )
            
            print(f"  状态码: {resp.status_code}")
            print(f"  响应长度: {len(resp.text)}")
            
            # 尝试解析
            try:
                data = resp.json()
                print(f"  ✓ JSON 响应")
                
                # 保存
                with open(f'/tmp/qunar_post_{date}_{i}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 数据已保存")
                
                # 查找价格
                data_str = json.dumps(data)
                prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', data_str)
                if prices:
                    unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                    print(f"  ✓ 找到价格: {unique_prices[:15]}")
                    return unique_prices
                else:
                    print(f"  预览: {json.dumps(data, ensure_ascii=False)[:200]}")
            
            except Exception as e:
                print(f"  ✗ 解析失败: {e}")
                print(f"  响应: {resp.text[:200]}")
        
        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
    
    return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 POST 价格接口测试")
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
