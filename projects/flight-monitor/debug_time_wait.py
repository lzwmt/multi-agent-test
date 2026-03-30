"""调试航班时间 - 等待AJAX加载"""
from playwright.sync_api import sync_playwright
import re

url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("1. 打开页面...")
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    
    print("2. 等待航班列表加载...")
    # 等待可能的航班列表元素
    try:
        # 等待包含航班信息的元素出现
        page.wait_for_selector('[class*="flight"], [class*="list"], [class*="item"]', timeout=20000)
        print("✓ 找到航班列表元素")
    except:
        print("✗ 未找到航班列表元素，继续等待...")
    
    # 等待更久
    page.wait_for_timeout(15000)
    
    print("3. 滚动页面加载更多...")
    # 滚动页面触发懒加载
    for i in range(3):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)
    
    print("4. 获取页面内容...")
    html = page.content()
    text = page.inner_text('body')
    
    browser.close()

print(f"\n页面长度: {len(html)}")

# 查找时间
print("\n=== 查找时间 ===")
times = re.findall(r'\b(\d{1,2}:\d{2})\b', text)
unique_times = sorted(set(times))
print(f"找到 {len(unique_times)} 个时间: {unique_times[:20]}")

# 查找价格和时间组合
print("\n=== 查找价格-时间组合 ===")
lines = text.split('\n')
for line in lines:
    line = line.strip()
    if re.search(r'\d{1,2}:\d{2}', line) and ('¥' in line or '元' in line or re.search(r'\d{3,4}', line)):
        if len(line) < 150:
            print(f"  {line[:100]}")
