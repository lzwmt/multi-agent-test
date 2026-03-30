"""直接调用去哪儿移动端 API"""
import requests
import json
import time
import random

# 移动端 API 基础 URL
BASE_URL = "https://m.flight.qunar.com"

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
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


def search_flights(dep_code: str, arr_code: str, date: str):
    """搜索航班"""
    print(f"\n{'='*70}")
    print(f"搜索: {dep_code} -> {arr_code}, 日期: {date}")
    print('='*70)
    
    # 尝试不同的 API 端点
    endpoints = [
        # 方案1: 搜索 API
        f"{BASE_URL}/touch/api/query?depCity={dep_code}&arrCity={arr_code}&depDate={date}&type=1",
        # 方案2: 列表 API
        f"{BASE_URL}/touch/api/flightlist?depCity={dep_code}&arrCity={arr_code}&depDate={date}",
        # 方案3: 价格 API
        f"{BASE_URL}/touch/api/price?depCity={dep_code}&arrCity={arr_code}&depDate={date}",
    ]
    
    for i, url in enumerate(endpoints, 1):
        print(f"\n尝试 API {i}: {url[:60]}...")
        
        try:
            time.sleep(random.uniform(1, 2))
            
            resp = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=30,
            )
            
            print(f"  状态码: {resp.status_code}")
            print(f"  响应长度: {len(resp.text)}")
            
            # 尝试解析 JSON
            try:
                data = resp.json()
                print(f"  响应类型: JSON")
                
                # 查找价格数据
                if isinstance(data, dict):
                    # 递归查找价格
                    def find_prices(obj, depth=0):
                        prices = []
                        if depth > 5:
                            return prices
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if 'price' in k.lower() and isinstance(v, (int, float)):
                                    if 200 <= v <= 5000:
                                        prices.append(v)
                                elif isinstance(v, (dict, list)):
                                    prices.extend(find_prices(v, depth+1))
                        elif isinstance(obj, list):
                            for item in obj:
                                prices.extend(find_prices(item, depth+1))
                        return prices
                    
                    prices = find_prices(data)
                    if prices:
                        unique_prices = sorted(set(prices))
                        print(f"  找到价格: {unique_prices[:10]}")
                        return unique_prices
                    else:
                        print(f"  未找到价格数据")
                        # 打印部分响应查看结构
                        print(f"  响应预览: {json.dumps(data, ensure_ascii=False)[:200]}")
                
            except:
                print(f"  响应不是 JSON，可能是 HTML")
                # 尝试从 HTML 中提取价格
                import re
                prices = re.findall(r'¥\s*([\d,]+)', resp.text)
                if prices:
                    unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
                    print(f"  从 HTML 找到价格: {unique_prices[:10]}")
                    return unique_prices
        
        except Exception as e:
            print(f"  错误: {e}")
    
    return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿移动端 API 直接调用")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        prices = search_flights('CAN', 'TAO', date_str)
        if prices:
            print(f"\n结果: {prices}")
