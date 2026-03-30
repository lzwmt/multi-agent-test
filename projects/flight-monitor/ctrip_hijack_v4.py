"""携程数据劫持器 V4 - 直接访问搜索结果页"""
import json
import time
from playwright.sync_api import sync_playwright


class CtripHijackFetcherV4:
    """携程数据劫持器 V4"""

    def __init__(self):
        self.api_data = None

    def fetch(self, dep_code, arr_code, date_str):
        """劫持携程航班数据"""
        print(f"\n{'='*70}")
        print(f"[携程劫持V4] {dep_code} -> {arr_code}, {date_str}")
        print('='*70)

        self.api_data = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    viewport={'width': 1280, 'height': 800},
                )

                page = context.new_page()

                # 劫持API响应
                def handle_response(response):
                    url = response.url
                    if 'batchSearch' in url and response.status == 200:
                        try:
                            data = response.json()
                            if data.get('data') and data['data'].get('flightItineraryList'):
                                self.api_data = data
                                print(f"\n✓ 劫持到API数据!")
                        except:
                            pass

                page.on('response', handle_response)

                # 直接访问搜索结果页
                url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
                print(f"\n访问: {url}")

                page.goto(url, wait_until='networkidle', timeout=60000)
                time.sleep(10)

                # 滚动触发加载
                print("滚动页面...")
                page.evaluate('window.scrollBy(0, 800)')
                time.sleep(5)

                # 等待API响应
                print("\n等待API响应...")
                for i in range(30):
                    if self.api_data:
                        break
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"  等待中... {i}s")

                browser.close()

                if self.api_data:
                    return self._parse_data(self.api_data)
                else:
                    print("✗ 未劫持到数据")
                    return None

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()
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
    fetcher = CtripHijackFetcherV4()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')

    if result:
        with open('/tmp/ctrip_v4_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ 数据已保存")
