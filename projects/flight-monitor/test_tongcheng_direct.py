"""测试同程直飞过滤"""
import requests
import json
import time


def test_tongcheng_direct(dep_code, arr_code, date_str):
    """测试同程直飞过滤"""
    print(f"\n{'='*70}")
    print(f"[同程直飞测试] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://m.ly.com',
        'Referer': 'https://m.ly.com/',
        'tcplat': '10060',
        'tcpolaris': '1',
    }
    
    timestamp = int(time.time() * 1000)
    headers['tcsessionid'] = f"0-{timestamp}"
    headers['tctracerid'] = f"test-{timestamp}"
    
    # 测试不同的pt参数
    # pt: 0=全部, 1=直飞, 2=中转
    test_cases = [
        {'pt': 0, 'desc': '全部航班'},
        {'pt': 1, 'desc': '仅直飞'},
        {'pt': 2, 'desc': '仅中转'},
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['desc']} (pt={case['pt']})")
        
        payload = {
            "acc": dep_code,
            "dcc": arr_code,
            "ddate": date_str,
            "cabin": 0,
            "pt": case['pt'],  # 过滤参数
            "entrance": 11,
            "pc": {"sd": date_str, "ed": date_str},
            "depAirport": None,
            "arrAirport": None
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('success'):
                    flight_data = data.get('data', {})
                    
                    # 获取航班数量
                    fs = flight_data.get('fs', [])
                    flight_count = len(fs)
                    
                    # 获取最低价格
                    lowest_price = flight_data.get('lp', 0)
                    
                    print(f"  ✓ 航班数: {flight_count}")
                    print(f"  ✓ 最低价格: ¥{lowest_price}")
                    
                    # 保存数据
                    with open(f'/tmp/tongcheng_pt{case["pt"]}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    print(f"  ✗ API失败")
            else:
                print(f"  ✗ HTTP错误: {resp.status_code}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    test_tongcheng_direct("CAN", "TAO", "2026-03-14")
