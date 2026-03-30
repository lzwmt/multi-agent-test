"""携程数据劫持器 V2 - 触发API加载"""
import json
import time
from playwright.sync_api import sync_playwright


class CtripHijackFetcherV2:
    """携程数据劫持器 V2"""

    def __init__(self):
        self.api_responses = []

    def fetch(self, dep_code, arr_code, date_str):
        """劫持携程航班数据"""
        print(f"\n{'='*70}")
        print(f"[携程劫持V2] {dep_code} -> {arr_code}, {date_str}")
        print('='*70)

        self.api_responses = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    viewport={'width': 1280, 'height': 800},
                )

                page = context.new_page()

                # 劫持所有响应
                def handle_response(response):
                    url = response.url
                    if 'ctrip' in url.lower():
                        try:
                            if 'batchsearch' in url.lower() or 'search' in url.lower():
                                data = response.json()
                                print(f"\n[API] {url[:60]}...")
                                self.api_responses.append({
                                    'url': url,
                                    'data': data
                                })
                        except:
                            pass

                page.on('response', handle_response)

                # 访问携程航班页面
                url = f"https://flights.ctrip.com/online/list/round-{dep_code.lower()}-{arr_code.lower()}?depdate={date_str}"
                print(f"\n访问: {url}")

                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)

                # 滚动页面触发加载
                print("滚动页面触发加载...")
                for i in range(5):
                    page.evaluate(f'window.scrollBy(0, 500)')
                    time.sleep(2)
                    print(f"  滚动 {i+1}/5")

                # 等待更多响应
                time.sleep(10)

                browser.close()

                # 分析结果
                print(f"\n{'='*70}")
                print(f"劫持到 {len(self.api_responses)} 个API响应")
                print('='*70)

                for i, resp in enumerate(self.api_responses[:5]):
                    print(f"\n{i+1}. {resp['url'][:80]}")
                    data = resp['data']
                    if isinstance(data, dict):
                        if 'flightItineraryList' in str(data):
                            print("  ✓ 包含航班数据")
                            # 保存
                            with open(f'/tmp/ctrip_hijack_{date_str}_{i}.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            return data

                return None

        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    fetcher = CtripHijackFetcherV2()
    result = fetcher.fetch('CAN', 'TAO', '2026-03-14')
