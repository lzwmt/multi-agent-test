"""调试去哪儿的时间信息"""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 打开首页
    page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(2000)
    
    # 填写出发地
    from_input = page.locator('[placeholder="出发地"]').first
    if from_input.is_visible():
        from_input.click()
        page.wait_for_timeout(500)
        from_input.fill("广州")
        page.wait_for_timeout(1000)
        page.locator('text=广州').first.click()
        page.wait_for_timeout(500)
    
    # 填写目的地
    to_input = page.locator('[placeholder="目的地"]').first
    if to_input.is_visible():
        to_input.click()
        page.wait_for_timeout(500)
        to_input.fill("青岛")
        page.wait_for_timeout(1000)
        page.locator('text=青岛').first.click()
        page.wait_for_timeout(500)
    
    # 点击搜索
    search_btn = page.locator('text=搜索').first
    if search_btn.is_visible():
        search_btn.click()
        page.wait_for_timeout(8000)
    
    # 获取文本内容
    text = page.inner_text('body')
    
    browser.close()

print("=== 去哪儿时间信息 ===")

# 查找时间
times = re.findall(r'\b(\d{1,2}:\d{2})\b', text)
unique_times = sorted(set(times))
print(f"找到 {len(unique_times)} 个时间: {unique_times[:20]}")

# 查找包含时间的行
lines = text.split('\n')
time_lines = []
for line in lines:
    line = line.strip()
    if re.search(r'\d{1,2}:\d{2}', line):
        # 查找同时包含价格和时间的行
        if ('¥' in line or '元' in line) and len(line) < 200:
            time_lines.append(line)

print(f"\n包含价格和时间的行 ({len(time_lines)} 行):")
for line in time_lines[:10]:
    print(f"  {line[:100]}")
