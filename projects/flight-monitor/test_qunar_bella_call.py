"""使用捕获的 Bella 签名调用 API"""
import requests
import json
import time

API_URL = "https://m.flight.qunar.com/flight/api/touchInnerList"

# 从劫持获取的参数
payload = {
    "arrCity": "青岛",
    "baby": "0",
    "cabinType": "0",
    "child": "0",
    "depCity": "广州",
    "from": "touch_index_search",
    "goDate": "2026-03-14",
    "firstRequest": True,
    "Bella": "1683616182042##03446241573e9ae333d509e7a6283656f65f8d18##iKohiK3wgMkMf-i0gUPwaUPsXuPwaUPwaUPwXwPwa5TQjOWxcI10aS30a=D0aS3mWSPOiK3siK3sWsWRXskTW=D=XsgNVPiIauPwawPwasD+WsasaSvNasXNaKa0aS30a2a0aSisyI0wcIkNiK3wiKWTiK3wWIj=fRDmjst=fSX+WIjOaMDAWRtOjS2OjSfUjsf2VR20aS30a2a0aSi=y-ELfuPwaUPsXuPwaUkGWuPmEukhXUkGWuPNawkTXukGWuPmWhkhEUkGWwkhEhPNaukGWUPNXwkhXukGWwkTWukTVhkGWUPNXwPmEhkGWuPmXukTauPwaUPwXwPwaMe0d-oxgMEsiK3wiKWTiK3wiKiRiPPAiKHGiPihiPPNiKtwiPDsiPPAiKt=iPiIiKiRiPPmiKtmiPGTiPP+iKHIiPGDiPPOiK0IiPDAiPPmiPGIiPDwiKiRiK3wiKiRiK3wfIksj+iQgCEQcOm0aS30a=D0aS30EKP0VDP0X230EKP0VKa0XPD0EKP0VRX0X2jpP-kbj-3bjOFeJukGVukTawPNEukGWUPNXwkhXukGWwkTWukTVhPwXwkGWwPmVukhVukGWhkhXUkhWwPwaUPwXwPwaMHxg+X0aS30a=D0aSieqMfLy9opohNno9NHgUNScO=0aS30a2a0aSisj+iQgCEKgMa0aS30a=D0WP30aSi+f9iwf-Wxo-iSfuNSq9W=iK3wiKiRiK3wjOFec9Fbq5GAcMGwd5pbjwPwaUPAEhP+Ehvt##bUSPC0opOM39R4cQFDBtp##arrCity,baby,cabinType,child,depCity,from,goDate,firstRequest",
    "startNum": 0,
    "sort": 5,
    "r": 1773320934909,
    "_v": 2,
    "underageOption": "",
    "st": 1773320934907,
    "__m__": "515bf222e174776a02c9c250f41fd299"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'Origin': 'https://m.flight.qunar.com',
    'Referer': 'https://m.flight.qunar.com/ncs/page/flightlist',
}

cookies = {
    'QN1': '000197002f107b4a06f0af1f',
    'QN48': '2c03fd02-5d77-4642-9ad0-c2281314ad27',
}


def call_with_bella():
    """使用 Bella 签名调用"""
    print("=" * 70)
    print("使用 Bella 签名调用 touchInnerList")
    print("=" * 70)
    
    try:
        time.sleep(1)
        
        resp = requests.post(
            API_URL,
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
                with open('/tmp/qunar_bella_result.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ 数据已保存")
                
                # 分析
                if 'data' in data:
                    if isinstance(data['data'], list):
                        print(f"\n找到 {len(data['data'])} 个航班")
                        for flight in data['data'][:3]:
                            print(f"  {json.dumps(flight, ensure_ascii=False)[:200]}")
                    else:
                        print(f"\n数据结构: {type(data['data'])}")
                        print(json.dumps(data['data'], ensure_ascii=False)[:500])
                
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
    call_with_bella()
