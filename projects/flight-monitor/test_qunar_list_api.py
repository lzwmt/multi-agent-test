"""拦截去哪儿航班列表 API"""
from playwright.sync_api import sync_playwright
import json
import time


def intercept_list_api(date_str: str):
    """拦截航班列表 API"""
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
            
            # 拦截请求
            def handle_route(route, request):
                url = request.url
                
                # 拦截列表相关 API
                if any(x in url.lower() for x in ['list', 'flight', 'search', 'query']) and request.method in ['GET', 'POST']:
                    print(f"\n[API] {request.method} {url[:80]}")
                    
                    # 记录请求
                    api_calls.append({
                        'url': url,
                        'method': request.method,
                        'headers': dict(request.headers),
                    })
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 访问列表页
            list_url = f"https://m.flight.qunar.com/h5/flight/list?dep=%E5%B9%BF%E5%B7%9E&arr=%E9%9D%92%E5%B2%9B&flightType=1&startDate={date_str}"
            print(f"访问: {list_url}")
            
            page.goto(list_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(15)  # 等待 API 调用
            
            browser.close()
            
            # 分析 API
            print(f"\n{'='*70}")
            print(f"拦截到 {len(api_calls)} 个 API 调用")
            print('='*70)
            
            for i, call in enumerate(api_calls[:10], 1):
                print(f"\n{i}. [{call['method']}] {call['url'][:80]}")
            
            return api_calls
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿航班列表 API 拦截")
    print("=" * 70)
    
    dates = ['2026-03-14']
    
    for date_str in dates:
        intercept_list_api(date_str)
