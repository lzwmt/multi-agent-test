"""携程数据劫持器 - 使用Playwright拦截API响应"""
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta


class CtripHijackFetcher:
    """携程数据劫持器"""

    def __init__(self):
        self.api_data = None

    def fetch(self, dep_code, arr_code, date_str):
        """劫持携程航班数据"""
        print(f"\n{'='*70}")
        print(f"[携程劫持] {dep_code} -> {arr_code}, {date_str}")
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
                                print(f"✓ 劫持到API数据: {len(data['data']['flightItineraryList'])} 个航班")
                        except:
                            pass

                page.on('response', handle_response)

                # 访问携程航班页面
                url = f"https://flights.ctrip.com/online/list/round-{dep_code.lower()}-{arr_code.lower()}?depdate={date_str}"
                print(f"\n访问: {url}")

                page.goto(url, wait_until='networkidle', timeout=60000)

                # 等待API响应
                print("等待API响应...")
                for i in range(30):  # 最多等待30秒
                    if self.api_data:
                        break
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"  等待中... {i}s")

                browser.close()

                if self.api_data:
                    return self._parse_data(self.api_data, dep_code, arr_code, date_str)
                else:
                    print("✗ 未劫持到数据")
                    return None

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_data(self, data, dep_code, arr_code, date_str):
        """解析携程数据"""
        flights = data['data']['flightItineraryList']

        result = {
            'source': 'ctrip',
            'departure': dep_code,
            'arrival': arr_code,
            'date': date_str,
            'flights': [],
            'min_price': 0,
        }

        prices = []

        for flight in flights:
            segments = flight.get('flightSegments', [])
            if not segments:
                continue

            segment = segments[0]

            # 只取直飞
            if segment.get('transferCount', 0) != 0:
                continue

            flight_list = segment.get('flightList', [])
            if not flight_list:
                continue

            f = flight_list[0]
            price_list = flight.get('priceList', [])

            if price_list:
                price = price_list[0].get('adultPrice', 0)

                # 过滤测试价格
                if price in [1000, 2000, 5000]:
                    continue

                if price > 0:
                    prices.append(price)

                    flight_info = {
                        'flight_no': f.get('flightNo', ''),
                        'airline': f.get('operateAirlineName') or f.get('marketAirlineName', ''),
                        'dep_time': f.get('departureDateTime', ''),
                        'arr_time': f.get('arrivalDateTime', ''),
                        'dep_airport': f.get('departureAirportName', ''),
                        'arr_airport': f.get('arrivalAirportName', ''),
                        'price': price,
                        'cabin': price_list[0].get('cabinName', ''),
                    }
                    result['flights'].append(flight_info)

        if prices:
            result['min_price'] = min(prices)

        print(f"\n✓ 解析完成:")
        print(f"  直飞航班: {len(result['flights'])} 个")
        print(f"  最低价格: ¥{result['min_price']}")

        # 显示前5个航班
        print(f"\n前5个航班:")
        for f in result['flights'][:5]:
            print(f"  {f['flight_no']}: {f['airline']} {f['dep_time'][11:16]} -> {f['arr_time'][11:16]} ¥{f['price']}")

        return result


def test_hijack():
    """测试劫持"""
    fetcher = CtripHijackFetcher()

    # 测试多日期
    dates = ['2026-03-14', '2026-03-15', '2026-03-17']

    for date in dates:
        result = fetcher.fetch('CAN', 'TAO', date)
        if result:
            # 保存数据
            with open(f'/tmp/ctrip_hijack_{date}.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        time.sleep(3)


if __name__ == "__main__":
    test_hijack()
