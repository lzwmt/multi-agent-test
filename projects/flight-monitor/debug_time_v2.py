"""调试航班时间 - 详细分析"""
from playwright.sync_api import sync_playwright
import re
import json

url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(10000)
    html = page.content()
    browser.close()

print(f"页面长度: {len(html)}")

# 保存HTML
with open('/tmp/ctrip_time.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\n=== 查找时间模式 ===")

# 方法1: 查找所有时间格式
time_pattern = r'\b(\d{1,2}:\d{2})\b'
times = re.findall(time_pattern, html)
unique_times = sorted(set(times))
print(f"找到 {len(unique_times)} 个唯一时间: {unique_times[:20]}")

# 方法2: 查找包含时间的JSON数据
print("\n=== 查找JSON中的时间 ===")
json_matches = re.findall(r'"(\d{2}:\d{2})"', html)
print(f"JSON中的时间: {sorted(set(json_matches))[:10]}")

# 方法3: 查找departure/arrival相关字段
print("\n=== 查找航班相关字段 ===")
flight_fields = [
    r'depTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
    r'arrTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
    r'departTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
    r'arriveTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
    r'startTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
    r'endTime["\']?\s*[:=]\s*["\']?(\d{1,2}:\d{2})',
]

for pattern in flight_fields:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"  匹配 {pattern[:30]}...: {sorted(set(matches))[:5]}")

# 方法4: 查找window.__INITIAL_STATE__
print("\n=== 查找初始状态数据 ===")
state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', html, re.DOTALL)
if state_match:
    print("✓ 找到 __INITIAL_STATE__")
    # 尝试提取时间信息
    state_html = state_match.group(1)
    times_in_state = re.findall(r'(\d{2}:\d{2})', state_html)
    print(f"  其中的时间: {sorted(set(times_in_state))[:10]}")
else:
    print("✗ 未找到 __INITIAL_STATE__")
