"""飞猪模拟点击搜索"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re
import time

# 飞猪 Cookie
fliggy_cookies = [
    {"name": "_cc_", "value": "WqG3DMC9EA%3D%3D", "url": "https://www.fliggy.com"},
    {"name": "_m_h5_tk", "value": "b6db5186f8b98b66d8399fb0047402d7_1773309556466", "url": "https://www.fliggy.com"},
    {"name": "_nk_", "value": "tb786549916278", "url": "https://www.fliggy.com"},
    {"name": "_tb_token_", "value": "ea394be481013", "url": "https://www.fliggy.com"},
    {"name": "cookie1", "value": "VTwvxo7TysEirwQVtaIUS733Fpx11mBbb2RBC1kWzT0%3D", "url": "https://www.fliggy.com"},
    {"name": "cookie2", "value": "1f00933a75453ffcf48541837301d565", "url": "https://www.fliggy.com"},
    {"name": "cna", "value": "om/GF8pRWTUCAXF3G6NXly8Y", "url": "https://www.fliggy.com"},
    {"name": "isg", "value": "BFhY9xRghYmkz6hKpfgRKl1XKYDqQbzLcvp7CpJJthNGLfgXOlQCW2kfY2UdJnSj", "url": "https://www.fliggy.com"},
    {"name": "lgc", "value": "tb786549916278", "url": "https://www.fliggy.com"},
    {"name": "tracknick", "value": "tb786549916278", "url": "https://www.fliggy.com"},
]


def fetch_fliggy_with_click(date_str: str):
    """使用模拟点击抓取飞猪"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(fliggy_cookies)
            print(f"✓ 已添加 {len(fliggy_cookies)} 个 Cookie")
            
            page = context.new_page()
            
            # 1. 打开飞猪首页
            print("1. 打开飞猪首页...")
            page.goto("https://www.fliggy.com/", wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # 2. 点击机票标签
            print("2. 查找机票入口...")
            flight_tab = page.locator('text=机票').first
            if flight_tab.is_visible():
                flight_tab.click()
                print("  ✓ 点击机票")
                page.wait_for_timeout(2000)
            
            # 3. 填写出发地
            print("3. 填写出发地...")
            from_input = page.locator('[placeholder*="出发"]').first
            if from_input.is_visible():
                from_input.click()
                page.wait_for_timeout(500)
                from_input.fill("广州")
                page.wait_for_timeout(1000)
                page.locator('text=广州').first.click()
                print("  ✓ 填写广州")
                page.wait_for_timeout(500)
            
            # 4. 填写目的地
            print("4. 填写目的地...")
            to_input = page.locator('[placeholder*="到达"]').first
            if to_input.is_visible():
                to_input.click()
                page.wait_for_timeout(500)
                to_input.fill("青岛")
                page.wait_for_timeout(1000)
                page.locator('text=青岛').first.click()
                print("  ✓ 填写青岛")
                page.wait_for_timeout(500)
            
            # 5. 设置日期
            print("5. 设置日期...")
            date_input = page.locator('[placeholder*="日期"]').first
            if date_input.is_visible():
                date_input.click()
                page.wait_for_timeout(500)
                # 尝试选择日期
                date_cell = page.locator(f'text={date_str}').first
                if date_cell.is_visible():
                    date_cell.click()
                    print(f"  ✓ 选择日期 {date_str}")
                else:
                    # 直接输入
                    date_input.fill(date_str)
                    print(f"  ✓ 输入日期 {date_str}")
                page.wait_for_timeout(1000)
            
            # 6. 点击搜索
            print("6. 点击搜索...")
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                search_btn.click()
                print("  ✓ 点击搜索")
                page.wait_for_timeout(15000)  # 等待结果加载
            
            # 7. 获取结果
            print("7. 获取结果...")
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
    print("飞猪模拟点击测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        prices = fetch_fliggy_with_click(date_str)
        if prices:
            print(f"\n结果: {prices}")
