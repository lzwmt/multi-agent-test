"""测试飞猪和同程价格抓取"""
import requests
import json
import time


def test_fliggy(dep_code, arr_code, date_str):
    """测试飞猪价格"""
    print(f"\n{'='*70}")
    print(f"[飞猪] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    # 飞猪H5 API
    url = "https://h5api.m.taobao.com/h5/mtop.alitrip.flight.flightsearch/1.0/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json',
        'Referer': 'https://h5.m.taobao.com/trip/flight/search/index.html',
    }
    
    params = {
        'depCity': dep_code,
        'arrCity': arr_code,
        'depDate': date_str,
        'type': '1',
    }
    
    try:
        time.sleep(1)
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
    except Exception as e:
        print(f"✗ 错误: {e}")


def test_tongcheng(dep_code, arr_code, date_str):
    """测试同程价格"""
    print(f"\n{'='*70}")
    print(f"[同程] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    # 同程H5 API
    url = "https://m.ly.com/flight/api/fightlist"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json',
        'Referer': 'https://m.ly.com/flight/',
    }
    
    params = {
        'dep': dep_code,
        'arr': arr_code,
        'date': date_str,
    }
    
    try:
        time.sleep(1)
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
    except Exception as e:
        print(f"✗ 错误: {e}")


if __name__ == "__main__":
    # 测试广州->青岛
    test_fliggy("CAN", "TAO", "2026-03-14")
    test_tongcheng("CAN", "TAO", "2026-03-14")
