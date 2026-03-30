"""搜索后劫持真正的航班列表 API"""
from playwright.sync_api import sync_playwright
import json
import time


def hijack_search_api(date_str: str):
    """劫持搜索后的 API"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    api_calls = []
    
    try:
        with sync_playwright() as p:
            iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=iphone_ua,
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 拦截所有 API 请求
            def handle_route(route, request):
                url = request.url
                
                # 拦截所有 POST API
                if '/api/' in url and request.method == 'POST':
                    post_data = request.post_data
                    if post_data:
                        try:
                            parsed = json.loads(post_data)
                            # 检查是否包含搜索相关参数
                            if any(x in str(parsed) for x in ['depCity', 'arrCity', '广州', '青岛', 'CAN', 'TAO']):
                                print(f"\n[搜索API] {url.split('/')[-1]}")
                                print(f"  POST: {json.dumps(parsed, ensure_ascii=False)[:300]}")
                                api_calls.append({
                                    'url': url,
                                    'data': parsed,
                                })
                        except:
                            pass
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 1. 访问 H5 页面
            print("1. 访问 H5 页面...")
            page.goto("https://m.flight.qunar.com/h5/flight/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            try:
                from_input = page.locator('input[placeholder*="出发"]').first
                if from_input.is_visible():
                    from_input.click()
                    time.sleep(1)
                    from_input.fill("广州")
                    time.sleep(1)
                    page.locator('text=广州').first.click()
                    time.sleep(1)
                    print("  ✓ 广州")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            try:
                to_input = page.locator('input[placeholder*="到达"]').first
                if to_input.is_visible():
                    to_input.click()
                    time.sleep(1)
                    to_input.fill("青岛")
                    time.sleep(1)
                    page.locator('text=青岛').first.click()
                    time.sleep(1)
                    print("  ✓ 青岛")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 4. 设置日期
            print("4. 设置日期...")
            try:
                date_input = page.locator('input[placeholder*="日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    time.sleep(1)
                    day = int(date_str.split('-')[2])
                    page.locator(f'text={day}日').first.click()
                    time.sleep(1)
                    print(f"  ✓ {date_str}")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 5. 点击搜索
            print("5. 点击搜索...")
            try:
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    print("  ✓ 已点击搜索")
                    time.sleep(15)
            except Exception as e:
                print(f"  ✗ {e}")
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(api_calls)} 个搜索 API")
            print('='*70)
            
            for i, call in enumerate(api_calls, 1):
                print(f"\n{i}. {call['url'].split('/')[-1]}")
                print(f"   参数: {json.dumps(call['data'], ensure_ascii=False, indent=2)[:400]}")
            
            return api_calls
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("劫持搜索 API 参数")
    print("=" * 70)
    
    dates = ['2026-03-14']
    
    for date_str in dates:
        hijack_search_api(date_str)
