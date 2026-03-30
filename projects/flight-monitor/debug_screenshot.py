"""截图查看页面实际内容"""
from playwright.sync_api import sync_playwright

url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("打开页面...")
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(10000)
    
    # 截图
    print("截图...")
    page.screenshot(path='/tmp/ctrip_screenshot.png', full_page=True)
    print("✓ 截图已保存: /tmp/ctrip_screenshot.png")
    
    # 获取页面标题
    title = page.title()
    print(f"页面标题: {title}")
    
    browser.close()
