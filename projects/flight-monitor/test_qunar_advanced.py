"""去哪儿高级拦截 - JSONP/WebSocket/影子请求"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random

# 存储所有请求
all_requests = []


def intercept_advanced(date_str: str):
    """高级拦截"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    global all_requests
    all_requests = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            )
            
            page = context.new_page()
            
            # 拦截所有请求
            def handle_request(request):
                url = request.url
                all_requests.append({
                    'url': url,
                    'method': request.method,
                    'type': request.resource_type,
                })
            
            # 拦截响应
            def handle_response(response):
                url = response.url
                
                # 检查 JSONP 请求（带 callback）
                if 'callback=' in url or 'jsonp' in url.lower():
                    print(f"[JSONP] {url[:100]}")
                
                # 检查 WebSocket
                if response.status == 101:
                    print(f"[WebSocket] {url}")
                
                # 检查可疑的日志/追踪请求
                if any(x in url.lower() for x in ['timetrack', 'commonlog', 'log.', 'track', 'analytics']):
                    try:
                        text = response.text()
                        if len(text) > 1000:  # 体积异常大的日志
                            print(f"[影子请求] {url[:80]} - 大小: {len(text)}")
                    except:
                        pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # 访问页面
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # 模拟真实交互
            print("\n模拟真实交互...")
            
            # 1. 填写出发地
            from_input = page.locator('[placeholder="出发地"]').first
            if from_input.is_visible():
                from_input.click()
                time.sleep(0.5)
                # 逐个字符输入
                for char in "广州":
                    from_input.type(char, delay=random.randint(50, 150))
                time.sleep(1)
                page.locator('text=广州').first.click()
                time.sleep(0.5)
            
            # 2. 填写目的地
            to_input = page.locator('[placeholder="目的地"]').first
            if to_input.is_visible():
                to_input.click()
                time.sleep(0.5)
                for char in "青岛":
                    to_input.type(char, delay=random.randint(50, 150))
                time.sleep(1)
                page.locator('text=青岛').first.click()
                time.sleep(0.5)
            
            # 3. 设置日期
            date_input = page.locator('[placeholder="出发日期"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(0.5)
                for char in date_str:
                    date_input.type(char, delay=random.randint(50, 150))
                time.sleep(1)
                page.locator('body').click()
                time.sleep(0.5)
            
            # 4. 滚动页面
            print("滚动页面...")
            page.mouse.wheel(0, 300)
            time.sleep(1)
            page.mouse.wheel(0, 300)
            time.sleep(1)
            
            # 5. 点击搜索
            print("点击搜索...")
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                # 模拟真实鼠标移动
                box = search_btn.bounding_box()
                if box:
                    page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(0.5)
                search_btn.click()
                print("  ✓ 已点击搜索")
            
            # 6. 等待并监听
            print("等待数据加载...")
            time.sleep(20)
            
            # 7. 再次滚动触发懒加载
            print("再次滚动...")
            for _ in range(3):
                page.mouse.wheel(0, 500)
                time.sleep(2)
            
            time.sleep(10)
            
            browser.close()
            
            # 分析请求
            print(f"\n{'='*70}")
            print("请求分析")
            print('='*70)
            
            # 查找可疑请求
            suspicious = []
            for req in all_requests:
                url = req['url']
                if any(x in url.lower() for x in ['callback', 'jsonp', 'api', 'query', 'search', 'price', 'flight']):
                    suspicious.append(req)
            
            print(f"\n可疑请求 ({len(suspicious)} 个):")
            for req in suspicious[:20]:
                print(f"  [{req['type']}] {req['method']} {req['url'][:80]}")
            
            return suspicious
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿高级拦截测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        intercept_advanced(date_str)
