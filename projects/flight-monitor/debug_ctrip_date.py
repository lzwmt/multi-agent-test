"""调试携程不同日期"""
from playwright.sync_api import sync_playwright
import re
from datetime import datetime, timedelta

def test_ctrip_date(date):
    date_str = date.strftime("%Y-%m-%d")
    url = f"https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate={date_str}"
    
    print(f"\n测试日期: {date_str}")
    print(f"URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(6000)
        
        html = page.content()
        browser.close()
    
    print(f"页面长度: {len(html)}")
    
    # 查找价格
    price_pattern = r'<div[^>]*class="[^"]*price[^"]*"[^>]*><dfn>¥</dfn>(\d+)'
    prices = re.findall(price_pattern, html)
    unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
    
    if unique_prices:
        print(f"✓ 找到价格: {unique_prices[:5]}")
    else:
        print("✗ 未找到价格")
        # 检查页面是否包含特定内容
        if 'CAN' in html and 'TAO' in html:
            print("  页面包含航线信息")
        if '航班' in html:
            print("  页面包含航班字样")
    
    return unique_prices

# 测试今天、明天、后天
today = datetime.now()
for i in range(3):
    date = today + timedelta(days=i)
    test_ctrip_date(date)
