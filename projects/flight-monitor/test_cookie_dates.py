"""使用 Cookie 测试多个日期"""
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import re

# Cookie 数据
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


def fetch_ctrip_price(date_str: str):
    """使用 Cookie 抓取携程价格"""
    url = f"https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate={date_str}"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(cookies_data)
            
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(8000)
            
            html = page.content()
            browser.close()
            
            # 提取价格
            prices = re.findall(r'<dfn>¥</dfn>(\d+)', html)
            unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 3000))
            
            return unique_prices
            
    except Exception as e:
        print(f"错误: {e}")
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("Cookie 测试 - 多个日期价格对比")
    print("=" * 70)
    
    # 测试未来7天
    dates = []
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    
    results = {}
    
    for date_str in dates:
        print(f"\n查询 {date_str}...")
        prices = fetch_ctrip_price(date_str)
        results[date_str] = prices
        
        if prices:
            print(f"  找到 {len(prices)} 个价格: ¥{min(prices)} - ¥{max(prices)}")
        else:
            print(f"  无数据")
    
    # 汇总对比
    print("\n" + "=" * 70)
    print("价格汇总对比")
    print("=" * 70)
    
    print(f"\n{'日期':<12} {'最低':<8} {'最高':<8} {'价格数量':<10} {'价格范围'}")
    print("-" * 70)
    
    for date_str in dates:
        prices = results.get(date_str, [])
        if prices:
            min_p = min(prices)
            max_p = max(prices)
            count = len(prices)
            range_str = f"¥{min_p}-{max_p}"
            print(f"{date_str:<12} ¥{min_p:<7} ¥{max_p:<7} {count:<10} {range_str}")
        else:
            print(f"{date_str:<12} 无数据")
    
    # 找出最低价日期
    print("\n" + "=" * 70)
    print("最低价排名")
    print("=" * 70)
    
    valid_results = [(d, min(p)) for d, p in results.items() if p]
    sorted_results = sorted(valid_results, key=lambda x: x[1])
    
    for i, (date_str, min_price) in enumerate(sorted_results[:5], 1):
        print(f"{i}. {date_str}: ¥{min_price}")
