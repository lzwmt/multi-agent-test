"""调试航班时间 - 从页面元素提取"""
from playwright.sync_api import sync_playwright
import re

url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(10000)
    
    print("=== 查找时间元素 ===")
    
    # 方法1: 查找包含时间的元素
    # 航班时间通常在特定 class 的元素中
    selectors = [
        '[class*="time"]',
        '[class*="flight"]',
        '[class*="depart"]',
        '[class*="arrive"]',
    ]
    
    for selector in selectors:
        elements = page.locator(selector).all()
        print(f"\n选择器 {selector}: 找到 {len(elements)} 个元素")
        
        for i, elem in enumerate(elements[:5]):
            text = elem.inner_text()
            if text and len(text) < 100:  # 只显示短文本
                print(f"  [{i}] {text[:50]}")
    
    # 方法2: 获取页面所有文本
    print("\n=== 页面文本中的时间 ===")
    all_text = page.inner_text('body')
    
    # 查找时间模式
    time_matches = re.findall(r'\b(\d{1,2}:\d{2})\b', all_text)
    unique_times = sorted(set(time_matches))
    print(f"找到 {len(unique_times)} 个唯一时间")
    print(f"前20个: {unique_times[:20]}")
    
    # 查找包含时间的行
    lines = all_text.split('\n')
    time_lines = [line.strip() for line in lines if re.search(r'\d{1,2}:\d{2}', line) and len(line.strip()) < 200]
    print(f"\n包含时间的文本行 ({len(time_lines)} 行):")
    for line in time_lines[:10]:
        print(f"  {line[:100]}")
    
    browser.close()
