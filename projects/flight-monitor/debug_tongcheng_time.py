"""调试同程的时间信息"""
from playwright.sync_api import sync_playwright
import re

url = "https://www.ly.com/Flight/QueryFlight.aspx?from=CAN&to=TAO&date=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(10000)
    
    # 获取文本内容
    text = page.inner_text('body')
    
    browser.close()

print("=== 同程时间信息 ===")

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
        if len(line) < 150:
            time_lines.append(line)

print(f"\n包含时间的文本行 ({len(time_lines)} 行):")
for line in time_lines[:15]:
    print(f"  {line[:100]}")
