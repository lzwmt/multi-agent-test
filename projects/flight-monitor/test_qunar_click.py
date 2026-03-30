"""去哪儿模拟点击搜索"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re
import time

# 去哪儿 Cookie
qunar_cookies = [
    {"name": "_i", "value": "DFiEZCOjLGiAUHPL_CeRItNt5MAw", "url": "https://flight.qunar.com"},
    {"name": "_q", "value": "U.uslsuus1942", "url": "https://flight.qunar.com"},
    {"name": "_s", "value": "s_MU6GVX5WXLHZZVXCE22PLRDX7A", "url": "https://flight.qunar.com"},
    {"name": "_t", "value": "29664446", "url": "https://flight.qunar.com"},
    {"name": "_v", "value": "WmNyo_iK8V1KVfy4mzpu3YZvOW7LhqMML7i4SyKLnmWOfk6XWZg_8BtrEbhBqYvF7b-wnYMgjnh9cVEp8IIpkKqGGRPVxQfZ-2gP1uAKKJGdow9hldmpSTExu_t1_Zhv2pcv_k7nqs5xAYe_lMbcd0XcVadY2S2BYTEpyapaV6bF", "url": "https://flight.qunar.com"},
    {"name": "csrfToken", "value": "HySpnjeJLVxoFFpcnIlvOIHnJNbxHhGc", "url": "https://flight.qunar.com"},
    {"name": "fid", "value": "b1c59615-0d7a-496c-abf8-838a0a4321b4", "url": "https://flight.qunar.com"},
]


def fetch_qunar_with_click(date_str: str):
    """使用模拟点击抓取去哪儿"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(qunar_cookies)
            print(f"✓ 已添加 {len(qunar_cookies)} 个 Cookie")
            
            page = context.new_page()
            
            # 1. 打开首页
            print("1. 打开去哪儿首页...")
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            from_input = page.locator('[placeholder="出发地"]').first
            if from_input.is_visible():
                from_input.click()
                time.sleep(0.5)
                from_input.fill("广州")
                time.sleep(1)
                page.locator('text=广州').first.click()
                print("  ✓ 填写广州")
                time.sleep(0.5)
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            to_input = page.locator('[placeholder="目的地"]').first
            if to_input.is_visible():
                to_input.click()
                time.sleep(0.5)
                to_input.fill("青岛")
                time.sleep(1)
                page.locator('text=青岛').first.click()
                print("  ✓ 填写青岛")
                time.sleep(0.5)
            
            # 4. 设置日期
            print("4. 设置日期...")
            date_input = page.locator('[placeholder="出发日期"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(0.5)
                date_input.fill(date_str)
                time.sleep(1)
                # 点击空白处关闭日期选择器
                page.locator('body').click()
                print(f"  ✓ 设置日期 {date_str}")
                time.sleep(0.5)
            
            # 5. 点击搜索
            print("5. 点击搜索...")
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                search_btn.click()
                print("  ✓ 点击搜索")
                time.sleep(15)  # 等待结果加载
            
            # 6. 获取结果
            print("6. 获取结果...")
            html = page.content()
            print(f"  页面长度: {len(html)}")
            
            title = page.title()
            print(f"  页面标题: {title}")
            
            # 查找价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"  找到价格: {unique_prices[:10]}")
            
            browser.close()
            return unique_prices
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿模拟点击测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        prices = fetch_qunar_with_click(date_str)
