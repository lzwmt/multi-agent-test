"""携程数据劫持器 V3 - 点击搜索触发API"""
import json
import time
from playwright.sync_api import sync_playwright


class CtripHijackFetcherV3:
    """携程数据劫持器 V3 - 模拟用户操作"""

    def __init__(self):
        self.api_data = None

    def fetch(self, dep_code, arr_code, date_str):
        """劫持携程航班数据"""
        print(f"\n{'='*70}")
        print(f"[携程劫持V3] {dep_code} -> {arr_code}, {date_str}")
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

                # 访问携程首页
                print("\n访问携程首页...")
                page.goto("https://flights.ctrip.com/", wait_until='networkidle', timeout=60000)
                time.sleep(3)

                # 填写出发地
                print("填写出发地...")
                try:
                    dep_input = page.locator('input[placeholder*="出发"]').first
                    if dep_input.is_visible():
                        dep_input.click()
                        time.sleep(1)
                        dep_input.fill(dep_code)
                        time.sleep(1)
                        # 选择第一个选项
                        page.locator(f'text={dep_code}').first.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"  出发地填写失败: {e}")

                # 填写目的地
                print("填写目的地...")
                try:
                    arr_input = page.locator('input[placeholder*="到达"]').first
                    if arr_input.is_visible():
                        arr_input.click()
                        time.sleep(1)
                        arr_input.fill(arr_code)
                        time.sleep(1)
                        page.locator(f'text={arr_code}').first.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"  目的地填写失败: {e}")

                # 选择日期
                print("选择日期...")
                try:
                    # 点击日期选择器
                    date_input = page.locator('[class*="date"]').first
                    if date_input.is_visible():
                        date_input.click()
                        time.sleep(1)
                        # 选择指定日期
                        page.locator(f'text={date_str}').first.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"  日期选择失败: {e}")

                # 点击搜索按钮
                print("点击搜索按钮...")
                try:
                    search_btn = page.locator('button:has-text("搜索")').first
                    if search_btn.is_visible():
                        search_btn.click()
                        print("  ✓ 已点击搜索")
                    else:
                        # 尝试其他选择器
                        search_btn = page.locator('[class*="search"]').first
                        if search_btn.is_visible():
                            search_btn.click()
                            print("  ✓ 已点击搜索(备选)")
                except Exception as e:
                    print(f"  搜索按钮点击失败: {e}")

                # 等待API响应
                print("\n等待API响应...")
                for i in range(60):  # 最多等待60秒
                    if self.api_data:
                        break
                    time.sleep(1)
                    if i % 10 == 0:
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
    fetcher = CtripHijackFetcherV3()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')

    if result:
        with open('/tmp/ctrip_v3_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ 数据已保存")
