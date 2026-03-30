"""拦截去哪儿 POST 请求数据"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import time


def intercept_post_data():
    """拦截 POST 请求数据"""
    print("=" * 70)
    print("拦截去哪儿 POST 请求")
    print("=" * 70)
    
    post_data = []
    
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
                
                # 只拦截价格相关 POST 请求
                if 'price' in url.lower() and request.method == 'POST':
                    print(f"\n[POST拦截] {url[:80]}")
                    print(f"  Method: {request.method}")
                    print(f"  Headers: {dict(request.headers)}")
                    
                    # 获取 POST 数据
                    post_data_text = request.post_data
                    if post_data_text:
                        print(f"  POST Data: {post_data_text[:500]}")
                        post_data.append({
                            'url': url,
                            'headers': dict(request.headers),
                            'data': post_data_text,
                        })
                    else:
                        print(f"  POST Data: (无)")
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 访问页面
            print("\n1. 访问页面...")
            page.goto("https://m.flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 填写信息
            print("2. 填写信息...")
            try:
                from_input = page.locator('input[placeholder*="出发"]').first
                if from_input.is_visible():
                    from_input.click()
                    time.sleep(1)
                    from_input.fill("广州")
                    time.sleep(1)
                    page.locator('text=广州').first.click()
                    time.sleep(1)
            except:
                pass
            
            try:
                to_input = page.locator('input[placeholder*="到达"]').first
                if to_input.is_visible():
                    to_input.click()
                    time.sleep(1)
                    to_input.fill("青岛")
                    time.sleep(1)
                    page.locator('text=青岛').first.click()
                    time.sleep(1)
            except:
                pass
            
            try:
                date_input = page.locator('input[placeholder*="日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    time.sleep(1)
                    page.locator('text=12日').first.click()
                    time.sleep(1)
            except:
                pass
            
            # 点击搜索
            print("3. 点击搜索...")
            try:
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    print("  ✓ 已点击搜索")
                    time.sleep(15)
            except:
                pass
            
            browser.close()
            
            # 分析拦截的数据
            print("\n" + "=" * 70)
            print("拦截结果")
            print("=" * 70)
            
            if post_data:
                print(f"\n✓ 拦截到 {len(post_data)} 个 POST 请求")
                for i, data in enumerate(post_data, 1):
                    print(f"\n请求 {i}:")
                    print(f"  URL: {data['url'][:80]}")
                    print(f"  POST Data: {data['data'][:300] if data['data'] else '(无)'}")
                    
                    # 尝试解析
                    try:
                        parsed = json.loads(data['data'])
                        print(f"  解析: {json.dumps(parsed, ensure_ascii=False, indent=2)[:300]}")
                    except:
                        pass
            else:
                print("\n✗ 未拦截到 POST 请求")
            
            return post_data
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    intercept_post_data()
