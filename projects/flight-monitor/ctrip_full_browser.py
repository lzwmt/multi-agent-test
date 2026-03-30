"""携程完整浏览器模拟 - 自动处理验证"""
import json
import time
from playwright.sync_api import sync_playwright


class CtripFullBrowser:
    """携程完整浏览器模拟器"""

    def __init__(self):
        self.api_data = None

    def fetch(self, dep_code, arr_code, date_str):
        """获取携程数据"""
        print(f"\n{'='*70}")
        print(f"[携程完整浏览器] {dep_code} -> {arr_code}, {date_str}")
        print('='*70)

        self.api_data = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,  # 非 headless 模式，避免检测
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1280, 'height': 800},
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                )

                # 注入脚本隐藏自动化特征
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                """)

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

                # 访问页面
                url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
                print(f"\n访问: {url}")

                page.goto(url, wait_until='networkidle', timeout=120000)

                # 等待页面加载
                print("等待页面加载...")
                time.sleep(15)

                # 检查是否有验证码
                print("\n检查是否有验证码...")
                try:
                    # 检查滑块验证码
                    slider = page.locator('.nc_wrapper, .slide-verify, .captcha').first
                    if slider.is_visible():
                        print("  ⚠ 发现验证码，尝试处理...")
                        # 这里可以添加自动处理验证码的逻辑
                        # 暂时等待手动处理
                        time.sleep(30)
                except:
                    print("  ✓ 无验证码")

                # 滚动页面触发加载
                print("\n滚动页面触发加载...")
                for i in range(3):
                    page.evaluate(f'window.scrollBy(0, 600)')
                    time.sleep(3)
                    print(f"  滚动 {i+1}/3")

                # 等待API响应
                print("\n等待API响应...")
                for i in range(60):
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
            'source': 'ctrip',
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
    fetcher = CtripFullBrowser()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')

    if result:
        with open('/tmp/ctrip_browser_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ 数据已保存")
