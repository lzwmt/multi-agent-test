"""使用正确的参数名调用同程API"""
import requests
import json


def call_tongcheng_correct():
    """使用正确的参数调用"""
    print(f"\n{'='*70}")
    print("[同程正确参数调用]")
    print('='*70)
    
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://m.ly.com/',
        'Origin': 'https://m.ly.com',
    }
    
    # 正确的参数结构
    payload = {
        "acc": "CAN",        # 出发地（注意参数名相反）
        "dcc": "TAO",        # 到达地
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
    
    print(f"\n请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
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
                
                # 检查是否正确的航线
                if flight_data.get('a') == 'CAN' and flight_data.get('d') == 'TAO':
                    print(f"\n🎉🎉🎉 成功获取广州->青岛数据!")
                    
                    # 获取价格日历
                    price_calendar = flight_data.get('pc', [])
                    print(f"\n价格日历 ({len(price_calendar)} 天):")
                    for item in price_calendar[:5]:
                        date = item.get('dd')
                        low = item.get('lp', 0)
                        high = item.get('hlp', 0)
                        print(f"  {date}: ¥{low} - ¥{high}")
                else:
                    print(f"\n⚠️ 返回的航线: {flight_data.get('a')} -> {flight_data.get('d')}")
                    print(f"   期望的航线: CAN -> TAO")
            else:
                print(f"✗ 失败: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"✗ HTTP错误: {resp.status_code}")
            
    except Exception as e:
        print(f"✗ 异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    call_tongcheng_correct()
