"""使用完整的Header信息调用同程API"""
import requests
import json


def call_tongcheng_with_headers():
    """使用完整的Header调用"""
    print(f"\n{'='*70}")
    print("[同程完整Header调用]")
    print('='*70)
    
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    # 完整的Headers（从劫持获取）
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://m.ly.com',
        'Referer': 'https://m.ly.com/',
        'tcplat': '10060',
        'tcpolaris': '1',
        'tcsessionid': '0-1773334574513',
        'tctracerid': '6128c2f0-1e34-11f1-817c-c1a6f17cdf0d',
    }
    
    # 请求参数
    payload = {
        "acc": "CAN",
        "dcc": "TAO",
        "ddate": "2026-03-14",
        "cabin": 0,
        "pt": 0,
        "entrance": 11,
        "pc": {
            "sd": "2026-03-13",
            "ed": "2026-03-27"
        },
        "depAirport": None,
        "arrAirport": None
    }
    
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            if data.get('success'):
                flight_data = data.get('data', {})
                
                print(f"\n✓ 成功!")
                print(f"  出发地: {flight_data.get('a')}")
                print(f"  到达地: {flight_data.get('d')}")
                print(f"  最低价格: ¥{flight_data.get('lp', 0)}")
                
                if flight_data.get('a') == 'CAN' and flight_data.get('d') == 'TAO':
                    print(f"\n🎉🎉🎉 成功!")
                    return True
                else:
                    print(f"\n⚠️ 航线不匹配")
            else:
                print(f"✗ 失败: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"✗ HTTP错误: {resp.status_code}")
            
    except Exception as e:
        print(f"✗ 异常: {e}")
    
    return False


if __name__ == "__main__":
    call_tongcheng_with_headers()
