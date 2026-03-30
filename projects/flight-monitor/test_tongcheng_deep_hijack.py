"""深度劫持同程所有API请求"""
import json
import time
from playwright.sync_api import sync_playwright


def deep_hijack_tongcheng(dep_code, arr_code, date_str):
    """深度劫持所有API"""
    print(f"\n{'='*70}")
    print(f"[同程深度劫持] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    all_requests = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 劫持所有请求
            def handle_route(route, request):
                url = request.url
                method = request.method
                
                # 关注所有API请求
                if any(x in url.lower() for x in ['api', 'flight', 'list', 'search', 'query', '17u', 'ly.com']):
                    try:
                        resp = request.response()
                        if resp:
                            content_type = resp.headers.get('content-type', '')
                            
                            # 检查是否是JSON或加密数据
                            if 'json' in content_type or 'text' in content_type:
                                try:
                                    text = resp.text()
                                    
                                    # 检查数据特征
                                    is_interesting = False
                                    if len(text) > 1000:  # 大数据量
                                        is_interesting = True
                                    if 'flight' in text.lower() or 'list' in text.lower():  # 包含关键词
                                        is_interesting = True
                                    if text.startswith('eyJ'):  # Base64编码的JSON
                                        is_interesting = True
                                    
                                    if is_interesting:
                                        print(f"\n[{method}] {url[:80]}...")
                                        print(f"  Content-Type: {content_type}")
                                        print(f"  长度: {len(text)}")
                                        
                                        all_requests.append({
                                            'url': url,
                                            'method': method,
                                            'content_type': content_type,
                                            'text': text[:500],
                                        })
                                except:
                                    pass
                    except:
                        pass
                
                route.continue_()
            
            page.route("**/*", handle_route)
            
            # 访问页面
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(10)
            
            # 滚动触发加载
            print("\n滚动页面触发加载...")
            for i in range(3):
                page.evaluate(f'window.scrollBy(0, 300)')
                time.sleep(3)
            
            time.sleep(5)
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(all_requests)} 个API请求")
            print('='*70)
            
            # 按URL排序并去重
            unique_requests = {}
            for req in all_requests:
                key = req['url'].split('?')[0]
                if key not in unique_requests:
                    unique_requests[key] = req
            
            for i, (key, req) in enumerate(unique_requests.items(), 1):
                print(f"\n{i}. [{req['method']}] {key}")
                print(f"   Content-Type: {req['content_type']}")
                print(f"   预览: {req['text'][:100]}")
            
            return all_requests
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    deep_hijack_tongcheng("CAN", "TAO", "2026-03-14")
