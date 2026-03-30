"""去哪儿 Cookie + 模拟点击 + 清除存储"""
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


def fetch_qunar_combo(date_str: str):
    """组合方案：Cookie + 模拟点击 + 清除存储"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    time.sleep(random.uniform(1, 3))
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-sandbox',
                    '--incognito',
                    '--disable-cache',
                    '--disable-application-cache',
                    '--disk-cache-size=0',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            
            # 添加 Cookie
            context.add_cookies(qunar_cookies)
            print(f"✓ 已添加 {len(qunar_cookies)} 个 Cookie")
            
            page = context.new_page()
            
            # 方法1: 尝试直接访问搜索结果页（带 Cookie）
            print("方法1: 直接访问搜索结果页...")
            url = f"https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=CAN&searchArrivalAirport=TAO&searchDepartureTime={date_str}&startSearch=true"
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(8)
            
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
        return []


def fetch_qunar_mobile(date_str: str):
    """尝试移动端页面"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str} (移动端)")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 375, 'height': 812},
            )
            
            context.add_cookies(qunar_cookies)
            
            page = context.new_page()
            
            # 移动端页面
            url = f"https://m.flight.qunar.com/?depCity=CAN&arrCity=TAO&date={date_str}"
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            html = page.content()
            print(f"  页面长度: {len(html)}")
            
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"  找到价格: {unique_prices[:10]}")
            
            browser.close()
            return unique_prices
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿组合方案测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    # 测试方案1: 组合方案
    print("\n【方案1: Cookie + 直接访问】")
    results1 = {}
    for date_str in dates:
        prices = fetch_qunar_combo(date_str)
        results1[date_str] = prices
    
    # 测试方案2: 移动端
    print("\n【方案2: 移动端页面】")
    results2 = {}
    for date_str in dates:
        prices = fetch_qunar_mobile(date_str)
        results2[date_str] = prices
    
    # 对比结果
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    print("\n方案1 (Cookie + 直接访问):")
    for date_str, prices in results1.items():
        print(f"  {date_str}: {prices[:5] if prices else '无数据'}")
    
    print("\n方案2 (移动端):")
    for date_str, prices in results2.items():
        print(f"  {date_str}: {prices[:5] if prices else '无数据'}")
