"""劫持同程POST请求参数"""
import json
import time
from playwright.sync_api import sync_playwright


def hijack_tongcheng_post():
    """劫持同程POST请求"""
    print(f"\n{'='*70}")
    print("[同程POST劫持]")
    print('='*70)
    
    post_requests = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 劫持请求
            def handle_route(route, request):
                url = request.url
                
                if 'preflights' in url and request.method == 'POST':
                    print(f"\n[POST请求] {url}")
                    print(f"  Headers: {dict(request.headers)}")
                    
                    post_data = request.post_data
                    if post_data:
                        print(f"  POST Data: {post_data[:500]}")
                        try:
                            parsed = json.loads(post_data)
                            print(f"\n  解析后的参数:")
                            print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            post_requests.append({
                                'url': url,
                                'data': parsed,
                            })
                        except:
                            print(f"  原始数据: {post_data}")
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 访问页面并搜索
            print("\n访问页面...")
            page.goto("https://m.ly.com/flight/itinerary?dep=CAN&arr=TAO&date=2026-03-14", 
                     wait_until='networkidle', timeout=30000)
            time.sleep(20)
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(post_requests)} 个POST请求")
            print('='*70)
            
            for i, req in enumerate(post_requests, 1):
                print(f"\n{i}. 参数结构:")
                print(json.dumps(req['data'], indent=2, ensure_ascii=False))
            
            return post_requests
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    hijack_tongcheng_post()
