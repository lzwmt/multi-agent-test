"""调试抓取 - 保存HTML分析"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    print("正在加载页面...")
    page.goto(url, wait_until='domcontentloaded', timeout=15000)
    page.wait_for_timeout(8000)
    
    html = page.content()
    browser.close()

# 保存HTML
with open('/tmp/ctrip_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML已保存，长度: {len(html)}")

# 查找可能的价格
print("\n查找 ¥ 符号附近的内容:")
yuan_matches = re.findall(r'.{0,30}¥.{0,30}', html)
for i, m in enumerate(yuan_matches[:20]):
    print(f"  {i+1}. {m}")

print("\n查找 price 关键字:")
price_matches = re.findall(r'.{0,50}[Pp]rice.{0,50}', html)
for i, m in enumerate(price_matches[:10]):
    print(f"  {i+1}. {m}")

# 查找3-4位数字
print("\n查找可能的价格数字(200-5000):")
numbers = re.findall(r'\b([2-9]\d{2,3})\b', html)
unique_nums = sorted(set(int(n) for n in numbers if 200 <= int(n) <= 5000))[:10]
print(f"  {unique_nums}")
