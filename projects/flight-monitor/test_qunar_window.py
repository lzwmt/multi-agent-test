"""去哪儿 - 检查 Window 全局变量和 Script 数据"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random


def check_window_data(date_str: str):
    """检查 Window 全局变量"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            )
            
            page = context.new_page()
            
            # 访问搜索结果页（直接构造 URL）
            search_url = f"https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=CAN&searchArrivalAirport=TAO&searchDepartureTime={date_str}&startSearch=true"
            print(f"访问: {search_url}")
            
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            time.sleep(10)  # 等待页面完全加载
            
            # 1. 检查 Window 全局变量
            print("\n1. 检查 Window 全局变量...")
            
            window_vars = [
                '__INITIAL_STATE__',
                '_pagedata',
                'flightData',
                '__flight__',
                '__DATA__',
                'initialState',
                'pageData',
                'QNR',
            ]
            
            for var in window_vars:
                try:
                    result = page.evaluate(f'() => {{ try {{ return window.{var}; }} catch(e) {{ return undefined; }} }}')
                    if result and result != {}:
                        print(f"  ✓ window.{var}: 找到数据 (类型: {type(result).__name__})")
                        # 如果是对象，尝试查找价格
                        if isinstance(result, dict):
                            result_str = json.dumps(result)
                            prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', result_str)
                            if prices:
                                print(f"    找到价格: {sorted(set(prices))[:10]}")
                    else:
                        print(f"  ✗ window.{var}: 无数据")
                except Exception as e:
                    print(f"  ✗ window.{var}: {e}")
            
            # 2. 检查 HTML 中的 script 标签
            print("\n2. 检查 HTML 中的 script 标签...")
            
            html = page.content()
            
            # 查找包含价格的 script
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            
            for i, script in enumerate(scripts[:10]):  # 只检查前10个
                if 'price' in script.lower() or 'flight' in script.lower():
                    # 查找价格
                    prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', script)
                    if prices:
                        print(f"  Script {i}: 找到价格 {sorted(set(prices))[:5]}")
                        # 打印部分内容
                        print(f"    内容预览: {script[:200]}")
            
            # 3. 检查特定 ID 的 script
            print("\n3. 检查特定 ID 的 script...")
            
            script_ids = ['flt-list-data', 'flight-data', 'initial-data', 'app-data']
            
            for sid in script_ids:
                try:
                    script = page.locator(f'script#{sid}').first
                    if script.is_visible():
                        text = script.inner_text()
                        print(f"  ✓ #{sid}: 找到")
                        print(f"    内容: {text[:200]}")
                except:
                    print(f"  ✗ #{sid}: 未找到")
            
            # 4. 搜索 HTML 中的价格
            print("\n4. 搜索 HTML 中的价格...")
            
            # 查找所有价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"  找到价格: {unique_prices[:20]}")
            
            # 5. 检查 URL 参数
            print("\n5. 检查当前 URL...")
            current_url = page.url
            print(f"  当前 URL: {current_url}")
            
            # 检查 URL 中是否包含日期
            if date_str.replace('-', '') in current_url or date_str in current_url:
                print(f"  ✓ URL 包含日期")
            else:
                print(f"  ⚠ URL 可能未包含日期（被重定向）")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 Window 数据检查")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        check_window_data(date_str)
