"""测试 AirLabs API"""
import requests
import json
from datetime import datetime

API_KEY = "3ad12eb5-3908-4c16-a844-343af49a3ea2"
BASE_URL = "https://airlabs.co/api/v9"

def test_airlabs():
    """测试 AirLabs API"""
    
    # 1. 测试航班查询
    print("=== 测试航班查询 ===")
    url = f"{BASE_URL}/flights"
    params = {
        'api_key': API_KEY,
        'dep_iata': 'CAN',  # 广州
        'arr_iata': 'TAO',  # 青岛
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        print(f"状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")
            
            if 'response' in data and data['response']:
                flights = data['response']
                print(f"\n找到 {len(flights)} 个航班")
                
                for f in flights[:3]:
                    print(f"\n航班: {f.get('flight_iata', 'N/A')}")
                    print(f"  起飞: {f.get('dep_time', 'N/A')}")
                    print(f"  到达: {f.get('arr_time', 'N/A')}")
                    print(f"  状态: {f.get('status', 'N/A')}")
            else:
                print("无航班数据")
        else:
            print(f"请求失败: {resp.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")

    # 2. 测试航线查询
    print("\n=== 测试航线查询 ===")
    url2 = f"{BASE_URL}/routes"
    params2 = {
        'api_key': API_KEY,
        'dep_iata': 'CAN',
        'arr_iata': 'TAO',
    }
    
    try:
        resp = requests.get(url2, params=params2, timeout=30)
        print(f"状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")
    except Exception as e:
        print(f"错误: {e}")

    # 3. 测试航班时刻表
    print("\n=== 测试航班时刻表 ===")
    url3 = f"{BASE_URL}/schedules"
    params3 = {
        'api_key': API_KEY,
        'dep_iata': 'CAN',
        'arr_iata': 'TAO',
        'date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    try:
        resp = requests.get(url3, params=params3, timeout=30)
        print(f"状态码: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    test_airlabs()
