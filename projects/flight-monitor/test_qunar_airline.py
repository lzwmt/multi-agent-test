"""调用去哪儿 getAirLine API 获取航班详情"""
import requests
import json
import time
import random

# API 端点
AIRLINE_API = "https://m.flight.qunar.com/lowFlightInterface/api/getAirLine"

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': '*/*',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://m.flight.qunar.com',
    'Referer': 'https://m.flight.qunar.com/h5/flight/',
}

# Cookie
cookies = {
    'QN1': '000197802f107b496f80bb26',
    'QN48': '000197802f107b496f80bb26',
    'Alina': 'c2440aac-c15f39-944f9e15-838fdb77-28b669b2a7f2',
}


def get_airline(dep_code: str, arr_code: str, date: str):
    """获取航班详情"""
    print(f"\n{'='*70}")
    print(f"getAirLine: {dep_code} -> {arr_code}, 日期: {date}")
    print('='*70)
    
    # 构造请求体
    payload = {
        "depCity": dep_code,
        "arrCity": arr_code,
        "depDate": date,
        "flightType": "1",
    }
    
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        time.sleep(random.uniform(1, 2))
        
        resp = requests.post(
            AIRLINE_API,
            headers=headers,
            cookies=cookies,
            json=payload,
            timeout=30,
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"✓ JSON 响应")
                
                # 保存
                with open(f'/tmp/qunar_airline_{date}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ 数据已保存到 /tmp/qunar_airline_{date}.json")
                
                # 分析数据结构
                print(f"\n数据结构分析:")
                print(f"  键: {list(data.keys())}")
                
                if 'data' in data:
                    print(f"  data 键: {list(data['data'].keys()) if isinstance(data['data'], dict) else type(data['data'])}")
                
                return data
            
            except Exception as e:
                print(f"✗ 解析失败: {e}")
                print(f"响应: {resp.text[:300]}")
        else:
            print(f"✗ 请求失败: {resp.status_code}")
            print(f"响应: {resp.text[:300]}")
    
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    return None


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 getAirLine API 测试")
    print("=" * 70)
    
    dates = ['2026-03-14', '2026-03-18']
    
    for date_str in dates:
        get_airline('CAN', 'TAO', date_str)
