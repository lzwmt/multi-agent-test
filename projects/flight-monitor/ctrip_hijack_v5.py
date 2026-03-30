"""携程数据劫持器 V5 - 使用浏览器Cookie调用API"""
import json
import time
import requests
from playwright.sync_api import sync_playwright


class CtripHijackFetcherV5:
    """携程数据劫持器 V5 - 获取浏览器Cookie后调用API"""

    def fetch(self, dep_code, arr_code, date_str):
        """获取携程数据"""
        print(f"\n{'='*70}")
        print(f"[携程V5] {dep_code} -> {arr_code}, {date_str}")
        print('='*70)

        try:
            # 第一步：用Playwright获取Cookie
            print("\n第一步：获取浏览器Cookie...")
            cookies = self._get_browser_cookies(dep_code, arr_code, date_str)

            if not cookies:
                print("✗ 获取Cookie失败")
                return None

            print(f"✓ 获取到 {len(cookies)} 个Cookie")

            # 第二步：用Cookie调用API
            print("\n第二步：调用API...")
            data = self._call_api(cookies, dep_code, arr_code, date_str)

            if data:
                return self._parse_data(data)
            else:
                print("✗ API调用失败")
                return None

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_browser_cookies(self, dep_code, arr_code, date_str):
        """获取浏览器Cookie"""
        cookies = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 800},
            )

            page = context.new_page()

            # 访问携程
            url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
            print(f"  访问: {url}")

            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(10)

            # 获取所有Cookie
            all_cookies = context.cookies()
            for cookie in all_cookies:
                cookies[cookie['name']] = cookie['value']

            browser.close()

        return cookies

    def _call_api(self, cookies, dep_code, arr_code, date_str):
        """调用携程API"""
        url = "https://flights.ctrip.com/international/search/api/search/batchSearch"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://flights.ctrip.com',
            'Referer': f'https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}',
        }

        payload = {
            "transactionID": f"{int(time.time()*1000)}_{dep_code.lower()}-{arr_code.lower()}_{int(time.time())}",
            "resourceVersion": "2026.03.14.13",
            "flightSegments": [
                {
                    "departureAirportCode": dep_code,
                    "arrivalAirportCode": arr_code,
                    "departureDate": date_str
                }
            ],
            "cabinClass": "Y",
            "adult": 1,
            "child": 0,
            "infant": 0
        }

        resp = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)
        print(f"  状态码: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('flightItineraryList'):
                print(f"  ✓ 成功! 返回 {len(data['data']['flightItineraryList'])} 个航班")
                return data
            else:
                print(f"  ✗ 无数据: {data.get('errorMessage', '未知错误')}")
        else:
            print(f"  ✗ 失败: {resp.text[:200]}")

        return None

    def _parse_data(self, data):
        """解析数据"""
        flights = data['data']['flightItineraryList']

        result = {
            'flights': [],
            'min_price': 0,
        }

        prices = []

        for flight in flights:
            segments = flight.get('flightSegments', [])
            if not segments:
                continue

            segment = segments[0]
            if segment.get('transferCount', 0) != 0:
                continue

            flight_list = segment.get('flightList', [])
            if not flight_list:
                continue

            f = flight_list[0]
            price_list = flight.get('priceList', [])

            if price_list:
                price = price_list[0].get('adultPrice', 0)
                if price > 0 and price not in [1000, 2000, 5000]:
                    prices.append(price)
                    result['flights'].append({
                        'flight_no': f.get('flightNo', ''),
                        'airline': f.get('operateAirlineName', ''),
                        'dep_time': f.get('departureDateTime', ''),
                        'arr_time': f.get('arrivalDateTime', ''),
                        'price': price,
                    })

        if prices:
            result['min_price'] = min(prices)

        print(f"\n✓ 解析完成: {len(result['flights'])} 个航班, 最低 ¥{result['min_price']}")
        return result


if __name__ == "__main__":
    fetcher = CtripHijackFetcherV5()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')

    if result:
        with open('/tmp/ctrip_v5_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ 数据已保存")
