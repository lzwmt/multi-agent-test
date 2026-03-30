"""使用 Cookie 登录的机票抓取器"""
from datetime import datetime
from typing import List, Dict, Optional
import json
import re
import time
import random

from playwright.sync_api import sync_playwright


class CookieFlightFetcher:
    """使用 Cookie 的机票抓取器"""
    
    def __init__(self, cookies: Dict = None):
        self.cookies = cookies or {}
    
    def fetch_ctrip_with_cookie(self, origin_code: str, dest_code: str, date: datetime, cookies: Dict) -> Optional[List[Dict]]:
        """使用 Cookie 从携程抓取"""
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://flights.ctrip.com/online/list/oneway-{origin_code}-{dest_code}?depdate={date_str}"
        
        print(f"  [Cookie] 抓取携程: {date_str}", end=" ")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                # 添加 Cookie
                if cookies:
                    context.add_cookies([{
                        'name': k,
                        'value': v,
                        'domain': '.ctrip.com',
                        'path': '/',
                    } for k, v in cookies.items()])
                
                page = context.new_page()
                
                # 访问页面
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(8000)
                
                html = page.content()
                browser.close()
                
                # 解析价格
                flights = self._extract_prices(html, date, 'ctrip')
                print(f"✓ {len(flights)}条")
                return flights
                
        except Exception as e:
            print(f"✗ {e}")
            return None
    
    def _extract_prices(self, html: str, date: datetime, source: str) -> List[Dict]:
        """提取价格"""
        flights = []
        unique_prices = set()
        
        # 查找价格模式
        patterns = [
            r'<dfn>¥</dfn>(\d+)',
            r'\u003cdfn\u003e¥\u003c/dfn\u003e(\d+)',
            r'"price"[^>]*>\s*<dfn>¥</dfn>(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = int(match)
                    if 200 <= price <= 2000 and price not in [1000, 2000, 5000]:
                        unique_prices.add(price)
                except:
                    pass
        
        for price in sorted(unique_prices)[:5]:
            flights.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'currency': 'CNY',
                'source': source,
            })
        
        return flights


def test_with_cookie():
    """测试使用 Cookie"""
    print("=" * 70)
    print("Cookie 登录测试")
    print("=" * 70)
    
    # 请提供 Cookie
    ctrip_cookies = {
        # 请在这里添加 Cookie
        # 'cookie_name': 'cookie_value',
    }
    
    if not ctrip_cookies:
        print("\n⚠️ 未提供 Cookie")
        print("请提供携程的 Cookie，格式如:")
        print("  ctrip_cookies = {")
        print("    'Session': 'xxx',")
        print("    'userToken': 'xxx',")
        print("    ...")
        print("  }")
        return
    
    fetcher = CookieFlightFetcher()
    
    # 测试两个日期
    dates = ['2026-03-12', '2026-03-14']
    
    for date_str in dates:
        print(f"\n{'='*70}")
        print(f"日期: {date_str}")
        print('='*70)
        
        date = datetime.strptime(date_str, '%Y-%m-%d')
        flights = fetcher.fetch_ctrip_with_cookie('CAN', 'TAO', date, ctrip_cookies)
        
        if flights:
            prices = [f['price'] for f in flights]
            print(f"价格: {prices}")
        else:
            print("无数据")


if __name__ == "__main__":
    test_with_cookie()
