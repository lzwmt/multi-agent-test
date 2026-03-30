"""调试页面中的JavaScript数据"""
from playwright.sync_api import sync_playwright
import re
import json

url = "https://www.ly.com/flights/home?from=CAN&to=TAO&date=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(10000)
    
    # 获取页面所有脚本内容
    scripts = page.locator('script').all()
    
    all_script_content = ""
    for script in scripts:
        content = script.inner_text()
        all_script_content += content + "\n"
    
    browser.close()

print(f"脚本总长度: {len(all_script_content)}")

# 在脚本中查找时间
print("\n=== 在脚本中查找时间 ===")
times = re.findall(r'(\d{2}:\d{2})', all_script_content)
unique_times = sorted(set(times))
print(f"找到 {len(unique_times)} 个时间: {unique_times[:20]}")

# 查找航班相关的JSON数据
print("\n=== 查找航班JSON数据 ===")
# 查找可能的航班数据
json_patterns = [
    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
    r'window\.__DATA__\s*=\s*({.+?});',
    r'var\s+flightData\s*=\s*({.+?});',
    r'"flightList":\s*(\[.+?\])',
    r'"flights":\s*(\[.+?\])',
]

for pattern in json_patterns:
    matches = re.findall(pattern, all_script_content, re.DOTALL)
    if matches:
        print(f"\n匹配模式: {pattern[:40]}...")
        print(f"找到 {len(matches)} 个匹配")
        
        # 尝试解析第一个匹配
        try:
            data = json.loads(matches[0])
            data_str = json.dumps(data)
            times_in_data = re.findall(r'(\d{2}:\d{2})', data_str)
            if times_in_data:
                print(f"其中的时间: {sorted(set(times_in_data))[:10]}")
        except:
            print("  无法解析JSON")
