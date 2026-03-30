"""使用 Cookie 测试携程"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re

# 从文件读取的 Cookie - 使用 URL 格式
cookies_data = [
    {"name": "_bfa", "value": "1.1773298447354.d448XhhHBfUO.1.1773298537519.1773298553036.1.10.102001", "url": "https://flights.ctrip.com"},
    {"name": "_bfaStatus", "value": "send", "url": "https://flights.ctrip.com"},
    {"name": "_ga", "value": "GA1.1.804476880.1773298553", "url": "https://flights.ctrip.com"},
    {"name": "GUID", "value": "09031036416118655147", "url": "https://flights.ctrip.com"},
    {"name": "DUID", "value": "u=3DFF547364985F3DEB3090547473BF20&v=0", "url": "https://flights.ctrip.com"},
    {"name": "cticket", "value": "05ADD5CC9E616FF981FDAF4AC031B5C1CA4E7BB33775BBBAF8156059A9DE675D", "url": "https://flights.ctrip.com"},
    {"name": "_udl", "value": "708D70C2B179E2F91CC5ED1C2CCE362D", "url": "https://flights.ctrip.com"},
    {"name": "login_uid", "value": "81691936B6783FD74467BB5E689E059B", "url": "https://flights.ctrip.com"},
    {"name": "login_type", "value": "0", "url": "https://flights.ctrip.com"},
    {"name": "IsNonUser", "value": "F", "url": "https://flights.ctrip.com"},
    {"name": "UBT_VID", "value": "1773298447354.d448XhhHBfUO", "url": "https://flights.ctrip.com"},
    {"name": "_RGUID", "value": "4e3823cf-2bda-476c-8658-0c6b5a12cda2", "url": "https://flights.ctrip.com"},
]


def fetch_ctrip_with_cookie(origin_code: str, dest_code: str, date_str: str):
    """使用 Cookie 抓取携程"""
    url = f"https://flights.ctrip.com/online/list/oneway-{origin_code}-{dest_code}?depdate={date_str}"
    
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print(f"URL: {url}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            # 添加 Cookie
            context.add_cookies(cookies_data)
            print(f"✓ 已添加 {len(cookies_data)} 个 Cookie")
            
            page = context.new_page()
            
            # 访问页面
            print("正在加载页面...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(10000)
            
            # 获取页面信息
            title = page.title()
            print(f"页面标题: {title}")
            
            html = page.content()
            print(f"页面长度: {len(html)}")
            
            # 查找价格
            prices = re.findall(r'<dfn>¥</dfn>(\d+)', html)
            unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 2000))
            print(f"找到价格: {unique_prices[:10]}")
            
            # 检查是否包含日期
            if date_str in html:
                print(f"✓ 页面包含日期 {date_str}")
            else:
                print(f"✗ 页面不包含日期 {date_str}")
            
            browser.close()
            
            return unique_prices
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("Cookie 登录测试 - 携程")
    print("=" * 70)
    
    # 测试两个日期
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    results = {}
    for date_str in dates:
        prices = fetch_ctrip_with_cookie('CAN', 'TAO', date_str)
        results[date_str] = prices
    
    # 对比结果
    print("\n" + "=" * 70)
    print("价格对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices}")
        else:
            print(f"{date_str}: 无数据")
