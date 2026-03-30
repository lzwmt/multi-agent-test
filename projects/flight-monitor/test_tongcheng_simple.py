"""简化版同程API测试"""
import requests
import json
import time


def test_tongcheng_list_api():
    """测试同程可能的列表API"""
    
    # 可能的API端点
    apis = [
        "https://wx.17u.cn/flightbffv2/book1/flightlist",
        "https://wx.17u.cn/flightbffv2/book1/list",
        "https://wx.17u.cn/flightbffv2/book1/search",
        "https://wx.17u.cn/flightbffv2/book1/query",
    ]
    
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
    
    payload = {
        "acc": "CAN",
        "dcc": "TAO",
        "ddate": "2026-03-14",
        "cabin": 0,
        "pt": 1,  # 仅直飞
        "entrance": 11,
        "pc": {"sd": "2026-03-14", "ed": "2026-03-14"},
        "depAirport": None,
        "arrAirport": None
    }
    
    for api in apis:
        print(f"\n{'='*70}")
        print(f"测试API: {api}")
        print('='*70)
        
        try:
            resp = requests.post(api, headers=headers, json=payload, timeout=10)
            print(f"状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data.get('success'):
                        print(f"✓ API可用!")
                        print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
                    else:
                        print(f"✗ API返回失败: {data.get('errorMessage', '未知错误')}")
                except:
                    print(f"响应: {resp.text[:500]}")
            else:
                print(f"✗ HTTP错误")
        except Exception as e:
            print(f"✗ 错误: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    test_tongcheng_list_api()
