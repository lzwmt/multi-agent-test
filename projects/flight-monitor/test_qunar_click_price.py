"""去哪儿 - 点击"查价"触发价格请求"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random


def fetch_price_by_click(date_str: str):
    """点击日期触发价格查询"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    api_calls = []
    
    try:
        with sync_playwright() as p:
            # iPhone User-Agent
            iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=iphone_ua,
                viewport={'width': 390, 'height': 844},
                device_scale_factor=3,
            )
            
            page = context.new_page()
            
            # 拦截所有请求
            def handle_request(request):
                url = request.url
                api_calls.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'type': request.resource_type,
                })
            
            def handle_response(response):
                url = response.url
                if 'price' in url.lower() or 'async' in url.lower():
                    try:
                        text = response.text()
                        print(f"[API响应] {url[:60]}... 长度: {len(text)}")
                    except:
                        pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # 访问 H5 首页
            print("1. 访问 H5 首页...")
            page.goto("https://m.flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 填写出发地
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
            
            # 填写目的地
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
            
            # 设置日期
            print("4. 设置日期...")
            try:
                date_input = page.locator('input[placeholder*="日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    time.sleep(1)
                    # 点击具体日期
                    day = int(date_str.split('-')[2])
                    page.locator(f'text={day}日').first.click()
                    time.sleep(1)
                    print(f"  ✓ {date_str}")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 点击搜索
            print("5. 点击搜索...")
            try:
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    print("  ✓ 已点击搜索")
                    time.sleep(10)
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 点击"查价"按钮
            print("6. 点击'查价'...")
            try:
                # 查找包含"查价"的元素
                price_btn = page.locator('text=查价').first
                if price_btn.is_visible():
                    print("  ✓ 找到'查价'按钮")
                    price_btn.click()
                    print("  ✓ 已点击'查价'")
                    time.sleep(10)
                else:
                    print("  ⚠ 未找到'查价'按钮")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 分析 API 调用
            print("\n7. API 调用分析...")
            
            # 查找价格相关请求
            price_requests = [call for call in api_calls if 'price' in call['url'].lower()]
            print(f"  找到 {len(price_requests)} 个 price 相关请求:")
            
            for req in price_requests[-10:]:  # 最后10个
                print(f"\n    [{req['method']}] {req['url'][:100]}")
                # 打印关键参数
                url = req['url']
                if '?' in url:
                    params = url.split('?')[1]
                    for param in params.split('&')[:5]:
                        if any(x in param.lower() for x in ['token', 'sign', '_v', 'key', 'auth']):
                            print(f"      🔑 {param[:60]}")
            
            browser.close()
            return price_requests
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿点击'查价'测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        fetch_price_by_click(date_str)
