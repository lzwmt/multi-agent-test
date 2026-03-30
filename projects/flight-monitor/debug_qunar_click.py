"""调试去哪儿 - 模拟点击搜索"""
from playwright.sync_api import sync_playwright
import re

url = "https://flight.qunar.com/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    print("1. 打开首页...")
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    print("2. 填写出发地...")
    # 点击出发地输入框
    from_input = page.locator('[placeholder="出发地"]').first
    if from_input.is_visible():
        from_input.click()
        page.wait_for_timeout(500)
        from_input.fill("广州")
        page.wait_for_timeout(1000)
        # 选择下拉项
        page.locator('text=广州 CAN').first.click()
        page.wait_for_timeout(500)
    
    print("3. 填写目的地...")
    to_input = page.locator('[placeholder="目的地"]').first
    if to_input.is_visible():
        to_input.click()
        page.wait_for_timeout(500)
        to_input.fill("青岛")
        page.wait_for_timeout(1000)
        page.locator('text=青岛 TAO').first.click()
        page.wait_for_timeout(500)
    
    print("4. 设置日期...")
    # 设置出发日期
    date_input = page.locator('[placeholder="出发日期"]').first
    if date_input.is_visible():
        date_input.click()
        page.wait_for_timeout(500)
        # 选择 2026-03-14
        page.locator('text=14').first.click()
        page.wait_for_timeout(500)
    
    print("5. 点击搜索...")
    search_btn = page.locator('text=搜索').first
    if search_btn.is_visible():
        search_btn.click()
        # 等待结果加载
        page.wait_for_timeout(10000)
    
    html = page.content()
    browser.close()

print(f"\n页面长度: {len(html)}")

# 保存HTML
with open('/tmp/qunar_click.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 查找价格
prices = re.findall(r'¥\s*([\d,]+)', html)
unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
if unique_prices:
    print(f"✓ 找到价格: {unique_prices}")
else:
    print("✗ 未找到价格")
    # 查找其他数字
    all_nums = re.findall(r'\b([2-9]\d{2,3})\b', html)
    print(f"  页面中的数字: {sorted(set(int(n) for n in all_nums))[:20]}")
