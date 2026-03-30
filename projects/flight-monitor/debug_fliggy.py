"""调试飞猪页面"""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    print("1. 打开飞猪首页...")
    page.goto("https://www.fliggy.com/", wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # 查找搜索表单
    print("\n2. 查找搜索表单元素...")
    
    # 找出发地输入框
    from_inputs = page.locator('input[placeholder*="出发"], input[placeholder*="城市"]').all()
    print(f"  找到 {len(from_inputs)} 个输入框")
    
    # 找搜索按钮
    search_btns = page.locator('button:has-text("搜索"), div:has-text("搜索机票"), span:has-text("搜索")').all()
    print(f"  找到 {len(search_btns)} 个搜索按钮")
    
    # 查看页面结构
    html = page.content()
    print(f"\n3. 页面长度: {len(html)}")
    
    # 保存HTML
    with open('/tmp/fliggy_home.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    browser.close()

print("\n4. 分析页面...")
# 查找机票相关链接
flight_links = re.findall(r'href="([^"]*flight[^"]*)"', html)
print(f"  找到 {len(flight_links)} 个机票链接")
for link in flight_links[:5]:
    print(f"    {link}")
