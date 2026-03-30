"""调试同程旅行"""
from playwright.sync_api import sync_playwright
import re

# 同程机票搜索URL
url = "https://www.ly.com/Flight/QueryFlight.aspx?from=CAN&to=TAO&date=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    print("正在打开同程...")
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(8000)
    
    html = page.content()
    print(f"页面长度: {len(html)}")
    
    # 保存HTML
    with open('/tmp/tongcheng.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    browser.close()

# 查找价格
print("\n查找价格...")
prices = re.findall(r'¥\s*([\d,]+)', html)
unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
if unique_prices:
    print(f"✓ 找到价格: {unique_prices[:10]}")
else:
    print("✗ 未找到价格")
    # 检查页面内容
    if '航班' in html or 'flight' in html.lower():
        print("  页面包含航班信息")
    else:
        print("  页面可能没有航班数据")
