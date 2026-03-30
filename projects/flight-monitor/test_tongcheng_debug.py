"""调试同程API参数"""
import requests
import json
import time
from datetime import datetime, timedelta


def test_tongcheng_params():
    """测试同程API不同参数"""
    
    # 测试不同参数组合
    test_cases = [
        {'dep': 'CAN', 'arr': 'TAO', 'date': '2026-03-14'},
        {'depCity': 'CAN', 'arrCity': 'TAO', 'depDate': '2026-03-14'},
        {'from': 'CAN', 'to': 'TAO', 'date': '2026-03-14'},
        {'departure': 'CAN', 'arrival': 'TAO', 'depDate': '2026-03-14'},
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json',
        'Referer': 'https://m.ly.com/',
        'Origin': 'https://m.ly.com',
    }
    
    # 从劫持的URL获取完整参数
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    # 尝试POST请求
    print("测试POST请求...")
    try:
        payload = {
            'dep': 'CAN',
            'arr': 'TAO',
            'date': '2026-03-14',
            'tripType': '1',
            'cabinType': '0',
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"POST状态码: {resp.status_code}")
        print(f"POST响应: {resp.text[:500]}")
    except Exception as e:
        print(f"POST错误: {e}")
    
    time.sleep(1)
    
    # 尝试GET请求带更多参数
    print("\n测试GET请求...")
    try:
        params = {
            'dep': 'CAN',
            'arr': 'TAO',
            'date': '2026-03-14',
            'tripType': '1',
            'cabinType': '0',
            'isHideFlight': '0',
            'isShare': '1',
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"GET状态码: {resp.status_code}")
        print(f"GET响应长度: {len(resp.text)}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                flight_data = data.get('data', {})
                print(f"出发地: {flight_data.get('a')}")
                print(f"到达地: {flight_data.get('d')}")
                print(f"最低价格: ¥{flight_data.get('lp', 0)}")
    except Exception as e:
        print(f"GET错误: {e}")


if __name__ == "__main__":
    test_tongcheng_params()
