"""刷新携程Cookie"""
import json
import time
from playwright.sync_api import sync_playwright


def refresh_ctrip_cookie():
    """刷新携程Cookie"""
    print("=== 刷新携程Cookie ===\n")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 800},
            )

            page = context.new_page()

            # 访问携程航班页面
            url = "https://flights.ctrip.com/online/list/round-can-tao?depdate=2026-03-14"
            print(f"访问: {url}")

            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(10)

            # 获取Cookie
            cookies = context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}

            print("\n获取到的Cookie:")
            important_cookies = ['_bfa', 'GUID', 'cticket', 'UBT_VID', '_RGUID']
            for name in important_cookies:
                if name in cookie_dict:
                    print(f"  {name}: {cookie_dict[name][:50]}...")

            # 保存Cookie
            with open('/tmp/ctrip_cookies.json', 'w') as f:
                json.dump(cookie_dict, f, indent=2)
            print("\n✓ Cookie已保存到 /tmp/ctrip_cookies.json")

            # 尝试调用API
            print("\n测试API...")

            # 使用新Cookie调用API
            import requests
            api_url = "https://flights.ctrip.com/international/search/api/search/batchSearch"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Origin': 'https://flights.ctrip.com',
                'Referer': 'https://flights.ctrip.com/online/list/round-can-tao',
            }

            payload = {
                "transactionID": f"{int(time.time()*1000)}_can-tao_1234",
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

            resp = requests.post(api_url, headers=headers, cookies=cookie_dict, json=payload, timeout=30)
            print(f"  状态码: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get('data') and data['data'].get('flightItineraryList'):
                    flights = data['data']['flightItineraryList']
                    print(f"  ✓ 成功！返回 {len(flights)} 个航班")

                    # 保存数据
                    with open('/tmp/ctrip_api_fresh.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print("  ✓ 数据已保存")
                else:
                    print(f"  ✗ 无数据: {data.get('errorMessage', '未知错误')}")
            else:
                print(f"  ✗ 失败: {resp.text[:200]}")

            browser.close()

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    refresh_ctrip_cookie()
