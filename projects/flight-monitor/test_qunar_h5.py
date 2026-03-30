"""去哪儿 H5 移动端强攻"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random


def fetch_qunar_h5(date_str: str):
    """H5 移动端抓取"""
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
                viewport={'width': 390, 'height': 844},  # iPhone 14
                device_scale_factor=3,
            )
            
            page = context.new_page()
            
            # 拦截所有请求
            def handle_request(request):
                url = request.url
                if 'price' in url.lower() or 'flight' in url.lower() or 'api' in url.lower():
                    api_calls.append({
                        'url': url,
                        'method': request.method,
                        'type': request.resource_type,
                    })
            
            page.on('request', handle_request)
            
            # 访问 H5 首页
            print("1. 访问 H5 首页...")
            page.goto("https://m.flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 截图查看页面
            page.screenshot(path=f'/tmp/qunar_h5_home_{date_str}.png')
            print("  ✓ 截图已保存")
            
            # 查找输入框
            print("2. 查找输入框...")
            
            # H5 页面可能有不同的选择器
            selectors = [
                'input[placeholder*="出发"]',
                'input[placeholder*="到达"]',
                '.from-city',
                '.to-city',
                '[data-type="from"]',
                '[data-type="to"]',
            ]
            
            for sel in selectors:
                try:
                    elem = page.locator(sel).first
                    if elem.is_visible():
                        print(f"  ✓ 找到: {sel}")
                except:
                    pass
            
            # 尝试填写出发地
            print("3. 填写出发地...")
            try:
                from_input = page.locator('input[placeholder*="出发"]').first
                if from_input.is_visible():
                    from_input.click()
                    time.sleep(1)
                    from_input.fill("广州")
                    time.sleep(1)
                    # 选择城市
                    page.locator('text=广州').first.click()
                    time.sleep(1)
                    print("  ✓ 广州")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 尝试填写目的地
            print("4. 填写目的地...")
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
            print("5. 设置日期...")
            try:
                date_input = page.locator('input[placeholder*="日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    time.sleep(1)
                    # 尝试点击具体日期
                    date_text = f"{int(date_str.split('-')[2])}日"
                    page.locator(f'text={date_text}').first.click()
                    time.sleep(1)
                    print(f"  ✓ {date_str}")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 点击搜索
            print("6. 点击搜索...")
            try:
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    print("  ✓ 已点击搜索")
                    time.sleep(15)
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 截图结果页
            page.screenshot(path=f'/tmp/qunar_h5_result_{date_str}.png')
            print("  ✓ 结果页截图已保存")
            
            # 分析 API 调用
            print("\n7. API 调用分析...")
            price_apis = [call for call in api_calls if 'price' in call['url'].lower()]
            print(f"  找到 {len(price_apis)} 个 price 相关 API:")
            for api in price_apis[:10]:
                print(f"    [{api['type']}] {api['url'][:80]}")
            
            # 提取 HTML 中的价格
            print("\n8. 提取价格...")
            html = page.content()
            
            # 多种价格模式
            prices = []
            prices.extend(re.findall(r'"price":\s*(\d+)', html))
            prices.extend(re.findall(r'price["\']?\s*[:=]\s*["\']?(\d+)', html))
            prices.extend(re.findall(r'¥\s*([\d,]+)', html))
            
            if prices:
                unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
                print(f"  ✓ 找到价格: {unique_prices[:15]}")
                return unique_prices
            else:
                print("  ✗ 未找到价格")
            
            browser.close()
            return []
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 H5 移动端测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    results = {}
    for date_str in dates:
        prices = fetch_qunar_h5(date_str)
        results[date_str] = prices
    
    # 对比结果
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices[:10]}")
        else:
            print(f"{date_str}: 无数据")
