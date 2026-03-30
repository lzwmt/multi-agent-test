"""调用 touchInnerList API"""
import requests
import json
import time

API_URL = "https://m.flight.qunar.com/touchInnerList"

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://m.flight.qunar.com',
    'Referer': 'https://m.flight.qunar.com/ncs/page/flightlist',
}

cookies = {
    'QN1': '000197002f107b49e940ddc8',
    'QN48': '000197002f107b49e940ddc8',
}


def call_touchinner(dep_city: str, arr_city: str, date: str):
    """调用 touchInnerList"""
    print(f"\n{'='*70}")
    print(f"touchInnerList: {dep_city} -> {arr_city}, {date}")
    print('='*70)
    
    # 构造参数
    payload = {
        "depCity": dep_city,
        "arrCity": arr_city,
        "goDate": date,
        "baby": "0",
        "cabinType": "0",
        "child": "0",
        "from": "touch_index_search",
        "firstRequest": "true",
        # Bella 参数需要动态生成，暂时省略
    }
    
    try:
        time.sleep(1)
        
        resp = requests.post(
            API_URL,
            headers=headers,
            cookies=cookies,
            data=payload,
            timeout=30,
        )
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"✓ JSON 响应")
                
                # 保存
                with open(f'/tmp/qunar_touchinner_{date}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ 数据已保存")
                
                # 分析
                if 'data' in data and isinstance(data['data'], list):
                    print(f"\n找到 {len(data['data'])} 个航班:")
                    for flight in data['data'][:3]:
                        print(f"  {json.dumps(flight, ensure_ascii=False)[:200]}")
                
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
    print("touchInnerList API 测试")
    print("=" * 70)
    
    # 测试广州-青岛
    call_touchinner("广州", "青岛", "2026-03-14")
    
    # 测试北京-上海（已知可用的参数）
    call_touchinner("北京", "上海", "2026-03-14")
