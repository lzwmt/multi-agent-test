"""测试飞猪 Cookie"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

# 飞猪 Cookie (来自 taobao.com)
fliggy_cookies = [
    {"name": "_cc_", "value": "WqG3DMC9EA%3D%3D", "url": "https://www.fliggy.com"},
    {"name": "_m_h5_tk", "value": "b6db5186f8b98b66d8399fb0047402d7_1773309556466", "url": "https://www.fliggy.com"},
    {"name": "_m_h5_tk_enc", "value": "cbf09ae98671fb356f937c461d6f8213", "url": "https://www.fliggy.com"},
    {"name": "_nk_", "value": "tb786549916278", "url": "https://www.fliggy.com"},
    {"name": "_tb_token_", "value": "ea394be481013", "url": "https://www.fliggy.com"},
    {"name": "cookie1", "value": "VTwvxo7TysEirwQVtaIUS733Fpx11mBbb2RBC1kWzT0%3D", "url": "https://www.fliggy.com"},
    {"name": "cookie2", "value": "1f00933a75453ffcf48541837301d565", "url": "https://www.fliggy.com"},
    {"name": "cna", "value": "om/GF8pRWTUCAXF3G6NXly8Y", "url": "https://www.fliggy.com"},
    {"name": "isg", "value": "BFhY9xRghYmkz6hKpfgRKl1XKYDqQbzLcvp7CpJJthNGLfgXOlQCW2kfY2UdJnSj", "url": "https://www.fliggy.com"},
    {"name": "lgc", "value": "tb786549916278", "url": "https://www.fliggy.com"},
    {"name": "tracknick", "value": "tb786549916278", "url": "https://www.fliggy.com"},
    {"name": "uc3", "value": "nk2=F5RCbbp6KYCLiG4p3F8%3D&id2=UUpjNFQhqxPXCIiXpg%3D%3D&lg2=WqG3DMC9VAQiUQ%3D%3D&vt3=F8dD29ZrJaFyoStRdSw%3D", "url": "https://www.fliggy.com"},
]


def fetch_fliggy_with_cookie(date_str: str):
    """使用 Cookie 抓取飞猪"""
    # 飞猪搜索 URL
    url = f"https://www.fliggy.com/?ttid=sem.000000736&needSearch=true&searchBy=1280&fromCity=CAN&toCity=TAO&depDate={date_str}"
    
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print(f"URL: {url}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(fliggy_cookies)
            print(f"✓ 已添加 {len(fliggy_cookies)} 个 Cookie")
            
            page = context.new_page()
            print("正在加载页面...")
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(10000)
            
            title = page.title()
            print(f"页面标题: {title}")
            
            html = page.content()
            print(f"页面长度: {len(html)}")
            
            # 查找价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"找到价格: {unique_prices[:10]}")
            
            browser.close()
            return unique_prices
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("飞猪 Cookie 测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    for date_str in dates:
        prices = fetch_fliggy_with_cookie(date_str)
