"""调试飞猪 - 直接访问搜索页"""
from playwright.sync_api import sync_playwright
import re

# 飞猪机票搜索URL（从浏览器复制的）
url = "https://s.fliggy.com/mipz/flight-search?tripType=0&depCity=CAN&arrCity=TAO&depDate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
    )
    page = context.new_page()
    
    print("正在打开飞猪搜索页...")
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(10000)  # 等待加载
    
    html = page.content()
    print(f"页面长度: {len(html)}")
    
    # 保存HTML
    with open('/tmp/fliggy_search.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    browser.close()

# 查找价格
print("\n查找价格...")
prices = re.findall(r'¥\s*([\d,]+)', html)
unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 100 <= int(p.replace(',', '')) <= 5000))
if unique_prices:
    print(f"✓ 找到价格: {unique_prices[:10]}")
else:
    print("✗ 未找到价格")
    # 查找其他数字
    all_nums = re.findall(r'\b([1-9]\d{2,3})\b', html)
    print(f"  页面中的数字: {sorted(set(int(n) for n in all_nums))[:20]}")
