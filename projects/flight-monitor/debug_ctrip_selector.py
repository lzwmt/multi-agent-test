"""调试携程价格选择器"""
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

print(f"页面长度: {len(html)}")

# 保存HTML用于分析
with open('/tmp/ctrip_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 查找各种价格模式
print("\n查找价格模式:")

# 模式1: 原来的 <dfn>¥</dfn> 格式
pattern1 = r'<div[^>]*class="[^"]*price[^"]*"[^>]*><dfn>¥</dfn>(\d+)'
matches1 = re.findall(pattern1, html)
print(f"1. <dfn>¥</dfn>格式: {len(matches1)} 个匹配")
if matches1:
    print(f"   价格: {matches1[:5]}")

# 模式2: 直接 ¥ 符号
pattern2 = r'[¥¥]\s*(\d{3,4})'
matches2 = re.findall(pattern2, html)
unique2 = sorted(set(int(m) for m in matches2 if 200 <= int(m) <= 5000))
print(f"2. ¥符号: {len(unique2)} 个唯一价格")
if unique2:
    print(f"   价格: {unique2[:10]}")

# 模式3: 低价日历格式
pattern3 = r'price:(\d+),date:\d{4}-\d{2}-\d{2}'
matches3 = re.findall(pattern3, html)
unique3 = sorted(set(int(m) for m in matches3 if 200 <= int(m) <= 5000))
print(f"3. 低价日历: {len(unique3)} 个唯一价格")
if unique3:
    print(f"   价格: {unique3[:10]}")

# 模式4: 查找所有3-4位数字
pattern4 = r'\b([2-9]\d{2,3})\b'
matches4 = re.findall(pattern4, html)
unique4 = sorted(set(int(m) for m in matches4 if 200 <= int(m) <= 5000))
print(f"4. 所有数字: {len(unique4)} 个唯一值")
print(f"   前20个: {unique4[:20]}")
