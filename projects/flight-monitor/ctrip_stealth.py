"""携程隐身模式 - 绕过检测"""
import json
import time
from playwright.sync_api import sync_playwright


class CtripStealthFetcher:
    """携程隐身获取器"""

    def __init__(self):
        self.api_data = None

    def fetch(self, dep_code, arr_code, date_str):
        """获取携程数据"""
        print(f"\n{'='*70}")
        print(f"[携程隐身模式] {dep_code} -> {arr_code}, {date_str}")
        print('='*70)

        self.api_data = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                )

                # 注入隐身脚本
                context.add_init_script("""
                    // 覆盖 webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });

                    // 覆盖 plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {name: 'Chrome PDF Plugin'},
                            {name: 'Chrome PDF Viewer'},
                            {name: 'Native Client'}
                        ],
                    });

                    // 覆盖 languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en'],
                    });

                    // 覆盖 platform
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32',
                    });

                    // 删除 automation 标记
                    delete navigator.__proto__.webdriver;
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

                # 等待
                print("等待页面加载...")
                time.sleep(20)

                # 滚动
                print("\n滚动页面...")
                for i in range(5):
                    page.evaluate(f'window.scrollBy(0, 500)')
                    time.sleep(2)

                # 等待API
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
    fetcher = CtripStealthFetcher()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')

    if result:
        with open('/tmp/ctrip_stealth_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ 数据已保存")
