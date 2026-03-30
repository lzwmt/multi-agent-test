"""检查日期参数是否生效"""
from playwright.sync_api import sync_playwright
from datetime import datetime

# 测试携程不同日期
def check_ctrip_dates():
    print("=== 检查携程日期 ===")
    
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    for date_str in dates:
        url = f"https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate={date_str}"
        print(f"\n日期: {date_str}")
        print(f"URL: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(5000)
            
            # 检查页面标题
            title = page.title()
            print(f"页面标题: {title}")
            
            # 检查页面中是否包含日期
            html = page.content()
            if date_str in html:
                print(f"✓ 页面包含日期 {date_str}")
            else:
                print(f"✗ 页面不包含日期 {date_str}")
            
            # 查找低价日历中的日期
            import re
            calendar_dates = re.findall(r'date:(\d{4}-\d{2}-\d{2})', html)
            if calendar_dates:
                print(f"低价日历日期: {sorted(set(calendar_dates))[:5]}")
            
            browser.close()

def check_tongcheng_dates():
    print("\n=== 检查同程日期 ===")
    
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        url = f"https://www.ly.com/flights/home?from=CAN&to=TAO&date={date_str}"
        print(f"\n日期: {date_str}")
        print(f"URL: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(5000)
            
            title = page.title()
            print(f"页面标题: {title}")
            
            html = page.content()
            if date_str in html:
                print(f"✓ 页面包含日期 {date_str}")
            else:
                print(f"✗ 页面不包含日期 {date_str}")
            
            browser.close()

if __name__ == "__main__":
    check_ctrip_dates()
    check_tongcheng_dates()
