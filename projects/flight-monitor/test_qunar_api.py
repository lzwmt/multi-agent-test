"""去哪儿 - 拦截 API 请求"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time

# 存储拦截到的请求
api_requests = []


def intercept_api(date_str: str):
    """拦截去哪儿的 API 请求"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    global api_requests
    api_requests = []
    
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
                if 'api' in url or 'query' in url or 'search' in url:
                    api_requests.append({
                        'url': url,
                        'method': request.method,
                        'headers': request.headers,
                    })
                    print(f"[请求] {request.method} {url[:80]}")
            
            # 拦截响应
            def handle_response(response):
                url = response.url
                if 'api' in url or 'query' in url or 'search' in url:
                    try:
                        if 'json' in response.headers.get('content-type', ''):
                            print(f"[响应] {url[:80]} - {response.status}")
                    except:
                        pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # 访问页面并操作
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # 填写出发地
            from_input = page.locator('[placeholder="出发地"]').first
            if from_input.is_visible():
                from_input.click()
                time.sleep(0.5)
                from_input.fill("广州")
                time.sleep(1)
                page.locator('text=广州').first.click()
                time.sleep(0.5)
            
            # 填写目的地
            to_input = page.locator('[placeholder="目的地"]').first
            if to_input.is_visible():
                to_input.click()
                time.sleep(0.5)
                to_input.fill("青岛")
                time.sleep(1)
                page.locator('text=青岛').first.click()
                time.sleep(0.5)
            
            # 设置日期
            date_input = page.locator('[placeholder="出发日期"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(0.5)
                # 清除并输入
                date_input.fill("")
                time.sleep(0.3)
                # 逐个字符输入
                for char in date_str:
                    date_input.type(char, delay=100)
                    time.sleep(0.2)
                time.sleep(1)
                page.locator('body').click()
                time.sleep(0.5)
            
            # 点击搜索
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                search_btn.click()
                print("\n点击搜索，等待 API 请求...")
                time.sleep(15)
            
            browser.close()
            
            # 分析拦截到的请求
            print(f"\n{'='*70}")
            print("拦截到的 API 请求:")
            print('='*70)
            
            for req in api_requests:
                print(f"\n方法: {req['method']}")
                print(f"URL: {req['url'][:100]}")
                if '?' in req['url']:
                    params = req['url'].split('?')[1]
                    print(f"参数: {params[:200]}")
            
            return api_requests
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 API 拦截测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        intercept_api(date_str)
