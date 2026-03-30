"""测试去哪儿 Cookie"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

# 去哪儿 Cookie
qunar_cookies = [
    {"name": "_i", "value": "DFiEZCOjLGiAUHPL_CeRItNt5MAw", "url": "https://flight.qunar.com"},
    {"name": "_q", "value": "U.uslsuus1942", "url": "https://flight.qunar.com"},
    {"name": "_s", "value": "s_MU6GVX5WXLHZZVXCE22PLRDX7A", "url": "https://flight.qunar.com"},
    {"name": "_t", "value": "29664446", "url": "https://flight.qunar.com"},
    {"name": "_v", "value": "WmNyo_iK8V1KVfy4mzpu3YZvOW7LhqMML7i4SyKLnmWOfk6XWZg_8BtrEbhBqYvF7b-wnYMgjnh9cVEp8IIpkKqGGRPVxQfZ-2gP1uAKKJGdow9hldmpSTExu_t1_Zhv2pcv_k7nqs5xAYe_lMbcd0XcVadY2S2BYTEpyapaV6bF", "url": "https://flight.qunar.com"},
    {"name": "_vi", "value": "yXacXwQ7NXqZ1HbTjo6w7JMHGFhnG4oYNiie3HnrYYaQq8JoGZzDnJrbkdvaYCGb6CILn-YJBUzy3UbbnsbkJmXX_QiK6InySXzTpoume4PJ6ppSA_MNMywBPSFIKRfqT6RBAo1dLgxN-aTAQavPDhSqF8YTl9kHD-9XrL7c2Gz8", "url": "https://flight.qunar.com"},
    {"name": "csrfToken", "value": "HySpnjeJLVxoFFpcnIlvOIHnJNbxHhGc", "url": "https://flight.qunar.com"},
    {"name": "fid", "value": "b1c59615-0d7a-496c-abf8-838a0a4321b4", "url": "https://flight.qunar.com"},
    {"name": "QN1", "value": "00014680306c7b477e204e0a", "url": "https://flight.qunar.com"},
    {"name": "QN42", "value": "%E5%8E%BB%E5%93%AA%E5%84%BF%E7%94%A8%E6%88%B7", "url": "https://flight.qunar.com"},
    {"name": "QN601", "value": "2d42f6012836d594698f0a355bee6d1a", "url": "https://flight.qunar.com"},
]


def fetch_qunar_with_cookie(date_str: str):
    """使用 Cookie 抓取去哪儿"""
    url = f"https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=CAN&searchArrivalAirport=TAO&searchDepartureTime={date_str}&startSearch=true"
    
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print(f"URL: {url}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(qunar_cookies)
            print(f"✓ 已添加 {len(qunar_cookies)} 个 Cookie")
            
            page = context.new_page()
            print("正在加载页面...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(10000)
            
            html = page.content()
            print(f"页面长度: {len(html)}")
            
            title = page.title()
            print(f"页面标题: {title}")
            
            # 查找价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"找到价格: {unique_prices[:10]}")
            
            browser.close()
            return unique_prices
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿 Cookie 测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    for date_str in dates:
        prices = fetch_qunar_with_cookie(date_str)
