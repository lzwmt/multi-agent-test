"""劫持去哪儿 getAirLine 请求参数"""
from playwright.sync_api import sync_playwright
import json
import time


def hijack_request(date_str: str):
    """劫持请求参数"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    requests = []
    
    try:
        with sync_playwright() as p:
            iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=iphone_ua,
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 拦截请求
            def handle_route(route, request):
                url = request.url
                
                if 'getAirLine' in url:
                    print(f"\n[getAirLine 请求]")
                    print(f"  URL: {url[:80]}")
                    print(f"  Method: {request.method}")
                    print(f"  Headers: {dict(request.headers)}")
                    
                    post_data = request.post_data
                    if post_data:
                        print(f"  POST Data: {post_data[:500]}")
                        try:
                            parsed = json.loads(post_data)
                            print(f"  解析: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
                        except:
                            pass
                    
                    requests.append({
                        'url': url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'data': post_data,
                    })
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 1. 访问首页
            print("1. 访问首页...")
            page.goto("https://m.flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
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
            
            # 总结
            print(f"\n{'='*70}")
            print(f"劫持到 {len(requests)} 个 getAirLine 请求")
            print('='*70)
            
            return requests
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("劫持 getAirLine 请求参数")
    print("=" * 70)
    
    dates = ['2026-03-14']
    
    for date_str in dates:
        hijack_request(date_str)
