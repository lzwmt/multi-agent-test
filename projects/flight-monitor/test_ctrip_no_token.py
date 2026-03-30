"""测试携程API不带token"""
import requests
import json
import time
import random


def test_ctrip_no_token():
    """测试不带token的请求"""
    print("=== 携程API测试（不带token）===\n")

    url = "https://flights.ctrip.com/international/search/api/search/batchSearch"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://flights.ctrip.com',
        'Referer': 'https://flights.ctrip.com/online/list/round-can-tao',
    }

    # 测试1: 完全不带cookie
    print("测试1: 完全不带Cookie...")
    payload = {
        "transactionID": f"{int(time.time()*1000)}_can-tao_{random.randint(1000,9999)}",
        "resourceVersion": "2026.03.14.13",
        "flightSegments": [
            {
                "departureAirportCode": "CAN",
                "arrivalAirportCode": "TAO",
                "departureDate": "2026-03-14"
            }
        ],
        "cabinClass": "Y",
        "adult": 1,
        "child": 0,
        "infant": 0
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('flightItineraryList'):
                print(f"  ✓ 成功！返回 {len(data['data']['flightItineraryList'])} 个航班")
            else:
                print(f"  ✗ 无数据: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"  ✗ 失败: {resp.text[:200]}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

    # 测试2: 只带基础cookie
    print("\n测试2: 只带基础Cookie...")
    basic_cookies = {
        'GUID': '09031036416118655147',
    }
    try:
        resp = requests.post(url, headers=headers, cookies=basic_cookies, json=payload, timeout=30)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('flightItineraryList'):
                print(f"  ✓ 成功！返回 {len(data['data']['flightItineraryList'])} 个航班")
            else:
                print(f"  ✗ 无数据: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"  ✗ 失败: {resp.text[:200]}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

    # 测试3: 带完整cookie
    print("\n测试3: 带完整Cookie...")
    full_cookies = {
        '_bfa': '1.1773298447354.d448XhhHBfUO.1.1773298537519.1773298553036.1.10.102001',
        'GUID': '09031036416118655147',
        'cticket': '05ADD5CC9E616FF981FDAF4AC031B5C1CA4E7BB33775BBBAF8156059A9DE675D',
        'UBT_VID': '1773298447354.d448XhhHBfUO',
        '_RGUID': '4e3823cf-2bda-476c-8658-0c6b5a12cda2',
    }
    try:
        resp = requests.post(url, headers=headers, cookies=full_cookies, json=payload, timeout=30)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('flightItineraryList'):
                print(f"  ✓ 成功！返回 {len(data['data']['flightItineraryList'])} 个航班")
            else:
                print(f"  ✗ 无数据: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"  ✗ 失败: {resp.text[:200]}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")


if __name__ == "__main__":
    test_ctrip_no_token()
