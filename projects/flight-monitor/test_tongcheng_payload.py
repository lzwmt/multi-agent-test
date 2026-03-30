"""深度调试同程请求载荷"""
import requests
import json
import time


def test_tongcheng_payload():
    """测试不同的请求载荷结构"""
    
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json',
        'Referer': 'https://m.ly.com/',
        'Origin': 'https://m.ly.com',
    }
    
    # 测试不同的payload结构
    payloads = [
        # 结构1: 直接参数
        {
            'dep': 'CAN',
            'arr': 'TAO',
            'date': '2026-03-14',
        },
        # 结构2: request包裹
        {
            'request': {
                'dep': 'CAN',
                'arr': 'TAO',
                'date': '2026-03-14',
            }
        },
        # 结构3: data包裹
        {
            'data': {
                'dep': 'CAN',
                'arr': 'TAO',
                'date': '2026-03-14',
            }
        },
        # 结构4: 完整参数
        {
            'dep': 'CAN',
            'arr': 'TAO',
            'date': '2026-03-14',
            'tripType': '1',
            'cabinType': '0',
            'isHideFlight': '0',
            'isShare': '1',
        },
        # 结构5: 使用城市ID（猜测）
        {
            'depCityId': '32',  # 广州
            'arrCityId': '7',   # 青岛
            'date': '2026-03-14',
        },
        # 结构6: 混合参数
        {
            'dep': 'CAN',
            'depCityId': '32',
            'arr': 'TAO',
            'arrCityId': '7',
            'date': '2026-03-14',
        },
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n{'='*70}")
        print(f"测试结构 {i}: {list(payload.keys())}")
        print('='*70)
        
        try:
            time.sleep(1)
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('success'):
                    flight_data = data.get('data', {})
                    print(f"✓ 成功!")
                    print(f"  出发地: {flight_data.get('a')}")
                    print(f"  到达地: {flight_data.get('d')}")
                    print(f"  最低价格: ¥{flight_data.get('lp', 0)}")
                    
                    if flight_data.get('a') == 'CAN' and flight_data.get('d') == 'TAO':
                        print(f"\n🎉 找到正确数据!")
                        return payload
                else:
                    print(f"✗ 失败: {data.get('errorMessage', '未知错误')}")
            else:
                print(f"✗ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"✗ 异常: {e}")
    
    return None


if __name__ == "__main__":
    correct_payload = test_tongcheng_payload()
    
    if correct_payload:
        print(f"\n{'='*70}")
        print("正确的Payload结构:")
        print('='*70)
        print(json.dumps(correct_payload, indent=2, ensure_ascii=False))
