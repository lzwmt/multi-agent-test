"""去哪儿模拟点击 - 隐身模式"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re
import time
import random

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

# 随机 User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
]


def fetch_qunar_stealth(date_str: str):
    """使用隐身模式抓取去哪儿"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    # 随机延迟
    time.sleep(random.uniform(2, 5))
    
    try:
        with sync_playwright() as p:
            # 隐身模式配置
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--incognito',
                    '--disable-cache',
                    '--disable-application-cache',
                    '--disk-cache-size=0',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                user_agent=random.choice(USER_AGENTS),
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            
            # 添加反检测脚本
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                window.chrome = { runtime: {} };
            """)
            
            context.add_cookies(qunar_cookies)
            print(f"✓ 已添加 {len(qunar_cookies)} 个 Cookie")
            
            page = context.new_page()
            
            # 1. 打开首页
            print("1. 打开去哪儿首页...")
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(3, 5))
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            from_input = page.locator('[placeholder="出发地"]').first
            if from_input.is_visible():
                from_input.click()
                time.sleep(random.uniform(0.5, 1))
                from_input.fill("广州")
                time.sleep(random.uniform(1, 2))
                page.locator('text=广州').first.click()
                print("  ✓ 填写广州")
                time.sleep(random.uniform(0.5, 1))
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            to_input = page.locator('[placeholder="目的地"]').first
            if to_input.is_visible():
                to_input.click()
                time.sleep(random.uniform(0.5, 1))
                to_input.fill("青岛")
                time.sleep(random.uniform(1, 2))
                page.locator('text=青岛').first.click()
                print("  ✓ 填写青岛")
                time.sleep(random.uniform(0.5, 1))
            
            # 4. 设置日期
            print("4. 设置日期...")
            date_input = page.locator('[placeholder="出发日期"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(random.uniform(0.5, 1))
                date_input.fill(date_str)
                time.sleep(random.uniform(1, 2))
                page.locator('body').click()
                print(f"  ✓ 设置日期 {date_str}")
                time.sleep(random.uniform(0.5, 1))
            
            # 5. 点击搜索
            print("5. 点击搜索...")
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                search_btn.click()
                print("  ✓ 点击搜索")
                time.sleep(random.uniform(12, 15))
            
            # 6. 获取结果
            print("6. 获取结果...")
            html = page.content()
            print(f"  页面长度: {len(html)}")
            
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
    print("去哪儿隐身模式测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    results = {}
    for date_str in dates:
        prices = fetch_qunar_stealth(date_str)
        results[date_str] = prices
    
    # 对比结果
    print("\n" + "=" * 70)
    print("价格对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices}")
        else:
            print(f"{date_str}: 无数据")
