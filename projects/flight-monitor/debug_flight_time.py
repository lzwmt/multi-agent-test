"""调试航班时间信息"""
from playwright.sync_api import sync_playwright
import re

# 测试携程
def check_ctrip():
    url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(8000)
        html = page.content()
        browser.close()
    
    print("=== 携程 ===")
    # 查找时间模式
    time_patterns = [
        r'(\d{2}:\d{2})',  # 时间格式 08:30
        r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})',  # 时间范围
    ]
    
    # 查找航班信息区域
    if 'flight' in html.lower() or '航班' in html:
        print("✓ 找到航班信息")
    
    # 查找时间
    times = re.findall(r'\b(\d{1,2}:\d{2})\b', html)
    unique_times = sorted(set(times))
    print(f"找到时间: {unique_times[:10]}")
    
    return html

# 测试同程
def check_tongcheng():
    url = "https://www.ly.com/Flight/QueryFlight.aspx?from=CAN&to=TAO&date=2026-03-14"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(8000)
        html = page.content()
        browser.close()
    
    print("\n=== 同程 ===")
    times = re.findall(r'\b(\d{1,2}:\d{2})\b', html)
    unique_times = sorted(set(times))
    print(f"找到时间: {unique_times[:10]}")
    
    return html

if __name__ == "__main__":
    check_ctrip()
    check_tongcheng()
